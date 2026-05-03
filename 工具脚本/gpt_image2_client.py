#!/usr/bin/env python3
"""
GPT Image 2 图片生成客户端
用于郴州旅游小红书号的自动化图片生成

支持功能：
1. 文本生成图片（text-to-image）
2. 参考图编辑（image editing with reference）
3. 批量生成
4. 风格预设

使用示例：
    python3 gpt_image2_client.py --prompt "郴州东江湖清晨薄雾" --output-dir ./output
    python3 gpt_image2_client.py --prompt "郴州高椅岭丹霞地貌赛博朋克风格" --ref-img 参考图路径 --output-dir ./output
    python3 gpt_image2_client.py --batch-prompts 批量prompt文件路径 --output-dir ./output
"""

import os
import sys
import json
import base64
import argparse
import datetime
from pathlib import Path

try:
    import openai
    from openai import OpenAI
except ImportError:
    print("ERROR: 需要安装 openai SDK: pip install openai")
    sys.exit(1)

# ==================== 配置 ====================

class GPTImage2Config:
    """GPT Image 2 配置"""
    
    API_BASE_URL = os.environ.get('GPT8080_BASE_URL', 'http://43.135.181.17:8080/v1')
    API_KEY = os.environ.get('GPT8080_API_KEY', '')
    MODEL = 'gpt-image-2'  # 或 'gpt-image-2'
    
    # 默认参数
    DEFAULT_QUALITY = 'medium'  # low, medium, high
    DEFAULT_FORMAT = 'jpeg'     # png, jpeg, webp
    DEFAULT_SIZE = '1024x1024'  # 或其他比例
    DEFAULT_COMPRESSION = 85
    DEFAULT_NEGATIVE_PROMPT = ''

    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        if not cls.API_KEY:
            print("ERROR: GPT8080_API_KEY 环境变量未设置")
            print("请在 /root/.hermes/.env 中配置或手动设置")
            return False
        print(f"✅ API Base URL: {cls.API_BASE_URL}")
        print(f"✅ API Key: {cls.API_KEY[:8]}...{cls.API_KEY[-4:]}")
        return True


# ==================== 风格预设 ====================

STYLE_PRESETS = {
    'travel_photo': {
        'name': '旅行摄影风',
        'prompt_suffix': '专业摄影，自然光，高分辨率，真实感，旅游杂志风格',
    },
    'watercolor': {
        'name': '国风水墨',
        'prompt_suffix': '中国传统水墨画风格，淡雅色调，留白意境',
    },
    'cyberpunk': {
        'name': '赛博朋克',
        'prompt_suffix': '赛博朋克风格，霓虹灯效，未来城市，高科技低生活',
    },
    'anime': {
        'name': '日系动漫',
        'prompt_suffix': '新海诚动画风格，明亮色彩，细节丰富，氛围感',
    },
    'oil_painting': {
        'name': '油画风格',
        'prompt_suffix': '印象派油画风格，厚涂技法，色彩丰富，光影对比',
    },
    'realistic_4k': {
        'name': '4K写实',
        'prompt_suffix': '超写实摄影，4K分辨率，电影级调色，专业级构图',
    },
    'xhs_tourism': {
        'name': '小红书旅游风',
        'prompt_suffix': '小红书热门旅游照片风格，温暖色调，人物入镜，打卡感',
    },
}


# ==================== 核心客户端 ====================

class GPTImage2Client:
    """GPT Image 2 API 客户端"""
    
    def __init__(self):
        if not GPTImage2Config.validate():
            raise ValueError("API配置不完整")
        
        self.client = OpenAI(
            api_key=GPTImage2Config.API_KEY,
            base_url=GPTImage2Config.API_BASE_URL,
        )
        self.model = GPTImage2Config.MODEL
        self.history = []
    
    def generate(
        self,
        prompt: str,
        style: str = None,
        negative_prompt: str = '',
        size: str = '1024x1024',
        quality: str = 'medium',
        output_format: str = 'jpeg',
        compression: int = 85,
        n: int = 1,
        reference_images: list = None,
        output_dir: str = './output',
        prefix: str = None,
    ):
        """
        生成图片
        
        Args:
            prompt: 生成提示词
            style: 风格预设名称（见STYLE_PRESETS）
            negative_prompt: 反向提示词
            size: 图片尺寸 (如 '1024x1024', '1024x1792')
            quality: 质量 (low/medium/high)
            output_format: 输出格式 (png/jpeg/webp)
            compression: JPEG压缩率 0-100
            n: 生成数量
            reference_images: 参考图路径列表（最多16张）
            output_dir: 输出目录
            prefix: 文件名前缀
        """
        # 应用风格预设
        if style and style in STYLE_PRESETS:
            style_info = STYLE_PRESETS[style]
            full_prompt = f"{prompt}，{style_info['prompt_suffix']}"
            print(f"🎨 风格: {style_info['name']}")
        else:
            full_prompt = prompt
        
        print(f"📝 Prompt: {full_prompt}")
        if negative_prompt:
            print(f"🚫 Negative: {negative_prompt}")
        print(f"📐 尺寸: {size} | 质量: {quality} | 数量: {n}")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 构建API参数
        api_params = {
            'model': self.model,
            'prompt': full_prompt,
            'n': n,
            'size': size,
            'quality': quality,
            'response_format': 'b64_json',  # 返回base64编码
        }
        
        # 添加负向提示（如果支持）
        if negative_prompt:
            api_params['negative_prompt'] = negative_prompt
        
        # 处理参考图（image editing模式）
        if reference_images and len(reference_images) > 0:
            ref_images = []
            for ref_path in reference_images[:16]:  # 最多16张
                if os.path.exists(ref_path):
                    with open(ref_path, 'rb') as f:
                        img_b64 = base64.b64encode(f.read()).decode('utf-8')
                    ref_images.append(f"data:image/jpeg;base64,{img_b64}")
                    print(f"📷 参考图: {ref_path}")
            
            if ref_images:
                api_params['image'] = ref_images[0]  # 主参考图
                if len(ref_images) > 1:
                    api_params['images'] = ref_images  # 多参考图
        
        try:
            print(f"⏳ 正在生成...")
            start_time = datetime.datetime.now()
            
            # 调用API
            response = self.client.images.generate(**api_params)
            
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            print(f"✅ 生成完成！耗时: {elapsed:.1f}s")
            
            # 保存图片
            saved_files = []
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for i, img_data in enumerate(response.data):
                if img_data.b64_json:
                    img_bytes = base64.b64decode(img_data.b64_json)
                    
                    # 生成文件名
                    if prefix:
                        filename = f"{prefix}_{timestamp}_{i+1}.{output_format}"
                    else:
                        filename = f"img_{timestamp}_{i+1}.{output_format}"
                    
                    file_path = output_path / filename
                    with open(file_path, 'wb') as f:
                        f.write(img_bytes)
                    
                    file_size = len(img_bytes) / 1024
                    print(f"💾 已保存: {file_path} ({file_size:.0f}KB)")
                    saved_files.append(str(file_path))
            
            # 记录历史
            self.history.append({
                'timestamp': timestamp,
                'prompt': full_prompt,
                'style': style,
                'size': size,
                'quality': quality,
                'elapsed': elapsed,
                'files': saved_files,
            })
            
            return saved_files
            
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
            
            # 如果是429错误，可能是API不支持image endpoint
            if '429' in str(e) or 'rate limit' in str(e).lower():
                print("💡 提示: 可能是API限流，请稍后重试")
            elif '404' in str(e):
                print("💡 提示: 该代理可能不支持 /images/generations 端点")
                print("💡 建议: 尝试使用OpenAI官方API或确认代理配置")
            
            raise
    
    def generate_batch(
        self,
        prompts: list,
        style: str = None,
        output_dir: str = './output',
        **kwargs
    ):
        """批量生成图片"""
        all_files = []
        print(f"🚀 批量生成: {len(prompts)} 个提示词")
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n{'='*50}")
            print(f"📋 [{i}/{len(prompts)}] {prompt}")
            
            prefix = f"batch_{i:03d}"
            files = self.generate(
                prompt=prompt,
                style=style,
                prefix=prefix,
                output_dir=output_dir,
                **kwargs
            )
            all_files.extend(files)
        
        print(f"\n{'='*50}")
        print(f"✅ 批量生成完成！共 {len(all_files)} 张图片")
        return all_files
    
    def save_history(self, output_path: str = None):
        """保存生成历史"""
        if not output_path:
            output_path = f"./output/history_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        
        print(f"📜 历史已保存: {output_path}")
        return output_path


# ==================== 郴州旅游预设 ====================

CHENZHOU_PRESETS = {
    'dongjiang_mist': {
        'name': '雾漫小东江',
        'prompt': '郴州东江湖清晨，薄雾笼罩江面，一叶扁舟划过水面，远处青山倒影，渔夫撒网',
        'style': 'travel_photo',
        'size': '1024x1792',  # 竖屏，适合小红书
    },
    'gaoyiling': {
        'name': '高椅岭丹霞',
        'prompt': '郴州高椅岭丹霞地貌，红色岩石纹理，无人机视角，壮观的龙脊地形',
        'style': 'realistic_4k',
        'size': '1024x1792',
    },
    'mangshan_forest': {
        'name': '莽山原始森林',
        'prompt': '郴州莽山原始森林，晨雾中的参天古树，阳光穿透树叶，神秘幽静',
        'style': 'watercolor',
        'size': '1024x1792',
    },
    'yangtianhu_grassland': {
        'name': '仰天湖草原',
        'prompt': '郴州仰天湖草原，绿草如茵，远处风力发电机，蓝天白云，开阔视野',
        'style': 'anime',
        'size': '1024x1792',
    },
    'chenzhou_cyberpunk': {
        'name': '赛博郴州',
        'prompt': '郴州城市夜景，霓虹灯照亮的老街，赛博朋克风格，未来感与传统碰撞',
        'style': 'cyberpunk',
        'size': '1024x1792',
    },
    'xhs_checkin': {
        'name': '小红书打卡风',
        'prompt': '年轻女性在郴州东江边打卡拍照，温暖色调，自然笑容，旅游博主风格',
        'style': 'xhs_tourism',
        'size': '1024x1792',
    },
}


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='GPT Image 2 图片生成客户端')
    parser.add_argument('--prompt', type=str, help='生成提示词')
    parser.add_argument('--batch-prompts', type=str, help='批量prompt文件路径（每行一个）')
    parser.add_argument('--style', type=str, choices=list(STYLE_PRESETS.keys()), 
                       help='风格预设')
    parser.add_argument('--preset', type=str, choices=list(CHENZHOU_PRESETS.keys()),
                       help='郴州旅游预设')
    parser.add_argument('--negative-prompt', type=str, default='', help='反向提示词')
    parser.add_argument('--size', type=str, default='1024x1024', help='图片尺寸')
    parser.add_argument('--quality', type=str, default='medium', 
                       choices=['low', 'medium', 'high'])
    parser.add_argument('--format', type=str, default='jpeg', 
                       choices=['png', 'jpeg', 'webp'])
    parser.add_argument('--n', type=int, default=1, help='生成数量')
    parser.add_argument('--ref-img', type=str, action='append', help='参考图路径（可多个）')
    parser.add_argument('--output-dir', type=str, default='./output', help='输出目录')
    parser.add_argument('--prefix', type=str, default=None, help='文件名前缀')
    
    args = parser.parse_args()
    
    # 创建客户端
    try:
        client = GPTImage2Client()
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 处理郴州预设
    if args.preset:
        preset = CHENZHOU_PRESETS[args.preset]
        print(f"🏞️ 使用郴州预设: {preset['name']}")
        args.prompt = preset['prompt']
        if not args.style:
            args.style = preset['style']
        args.size = preset['size']
    
    # 处理批量生成
    if args.batch_prompts:
        with open(args.batch_prompts, 'r', encoding='utf-8') as f:
            prompts = [line.strip() for line in f if line.strip()]
        
        client.generate_batch(
            prompts=prompts,
            style=args.style,
            output_dir=args.output_dir,
            negative_prompt=args.negative_prompt,
            size=args.size,
            quality=args.quality,
            output_format=args.format,
        )
    
    # 处理单个生成
    elif args.prompt:
        client.generate(
            prompt=args.prompt,
            style=args.style,
            negative_prompt=args.negative_prompt,
            size=args.size,
            quality=args.quality,
            output_format=args.format,
            n=args.n,
            reference_images=args.ref_img,
            output_dir=args.output_dir,
            prefix=args.prefix,
        )
    
    else:
        # 默认演示模式
        print("🚀 默认演示: 生成郴州东江湖图片")
        client.generate(
            prompt="郴州东江湖清晨，薄雾笼罩江面，一叶扁舟划过水面，渔夫撒网，远处青山倒影",
            style='travel_photo',
            size='1024x1792',
            quality='medium',
            n=2,
            output_dir='./output',
        )
    
    # 保存历史
    client.save_history()


if __name__ == '__main__':
    main()

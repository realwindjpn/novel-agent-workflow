#!/usr/bin/env python3
from pathlib import Path
p=Path('/root/workspace/科武纪元/新版/第241章.md')
s=p.read_text(encoding='utf-8')
# Fix 1: remove compilation contradiction - replace all compilation references with pre-built extraction
s=s.replace('脚本开始跑。树莓派的风扇转速上去了，嗡嗡声比之前大了不少。CPU温度从四十二度升到六十七度。进度条走得慢。ARM架构编译C++代码本来就不快，树莓派的散热也一般。','')
s=s.replace('他写了个安装脚本。脚本的逻辑是：先装依赖库，再克隆open5GS和srsRAN的GitHub仓库，然后分别编译。整个过程不联网，依赖库和源码都存在离线电脑的一个隔离包里——三年前林泽远准备安全屋的时候，大概就把这些工具也备好了。','')
s=s.replace('脚本开始跑','解压开始跑')
s=s.replace('open5GS的核心网模块已经编到73%。srsRAN还在克隆仓库。','open5GS的核心网解压到了90%。srsRAN的基站软件还在解压。')
# Fix 2: clarify this is DNS honey pot via WiFi, not cellular TX
s=s.replace('他写了个安装脚本。脚本的逻辑是：先装依赖库，再克隆open5GS和srsRAN的GitHub仓库，然后分别编译。整个过程不联网，依赖库和源码都存在离线电脑的一个隔离包里——三年前林泽远准备安全屋的时候，大概就把这些工具也备好了。\n\n脚本开始跑。树莓派的风扇转速上去了，嗡嗡声比之前大了不少。CPU温度从四十二度升到六十七度。进度条走得慢。ARM架构编译C++代码本来就不快，树莓派的散热也一般。林泽远从抽屉里翻出一个小USB风扇，插在树莓派旁边，对着CPU那片吹。风速不大，但至少能让热气散得快一点。\n\n"多久？"林星辰问。\n\n"四十分钟到一小时。"林泽远说，"你先把手机装回去。"',
'"这个不需要联网。"林泽远说，"三年前我就把交叉编译好的镜像放在安全屋里了。直接解压。"\n\n他从离线电脑的隔离包里拖出一个tar.gz，解压到树莓派的系统盘里。open5GS的核心网和srsRAN的基站软件都在里面。预编译的ARM二进制。不需要等编译。\n\n树莓派的风扇嗡嗡转着。解压进度条走得很快。')
# Fix 3: clarify the honey pot approach - WiFi DNS spoof, not cellular TX power issue
s=s.replace('"树莓派可以模拟一个完整的蜂窝网络环境。用open5GS搭建核心网，用srsRAN做基带。手机以为自己在连运营商网络，实际上所有流量都经过树莓派。我们能看到它发出的每一个包。"',
'"树莓派开一个WiFi热点。手机连上来之后，我把DNS指向树莓派自己的DNS服务器。它以为自己在连运营商网络，实际上所有DNS查询都经过树莓派。我们能看到它发出的每一个请求。"他顿了顿，"不用模拟蜂窝网络。WiFi就够了。手机在安全屋里，离树莓派只有三十厘米。信号强度不是问题。"')
p.write_text(s,encoding='utf-8')
chars=sum(1 for c in s if '\u4e00'<=c<='\u9fff')
print('chars',chars)

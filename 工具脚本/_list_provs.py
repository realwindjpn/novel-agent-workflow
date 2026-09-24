import yaml
c = yaml.safe_load(open('/root/.hermes/config.yaml'))
provs = c.get('providers', {})
for name in ['gorouter','gorouter-backup','xlabs','stepfun','siliconflow',
             'nexotoken-general','nexotoken-openai','openrouter','nim','openfly',
             'nineone','centos-hk','muyuan','deepwhale','astra','astrdark',
             'ds2api','wahuiliyi','wahuiliyi-ds','zening','tokenrouter']:
    p = provs.get(name)
    if p:
        print(name, '|', p.get('api_mode') or p.get('backend'), '|',
              p.get('default_model') or p.get('model'), '|', p.get('base_url'))

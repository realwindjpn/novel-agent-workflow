import yaml
c = yaml.safe_load(open('/root/.hermes/config.yaml'))
provs = c.get('providers', {})
# print all providers with their model + api_mode + base_url
for name in sorted(provs.keys()):
    p = provs[name]
    print(name, '|', p.get('api_mode') or p.get('backend'), '|',
          p.get('default_model') or p.get('model'), '|', p.get('base_url'))

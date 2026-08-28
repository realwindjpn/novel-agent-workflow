import yaml, json
c = yaml.safe_load(open('/root/.hermes/config.yaml'))
p = c.get('providers', {}) or {}
targets = ['sotamodel', 'nous', 'tokenrhythm-dsv4', 'chun-grok46', 'any', 'agentrouter']
for k in targets:
    v = p.get(k)
    if not v:
        print(k, '-> MISSING')
    else:
        print(k, '->', v.get('base_url', ''), '| default:', v.get('default_model', ''), '| key_env:', v.get('api_key_env', v.get('env_key', '')))
print('--- ALL ---')
print(json.dumps(sorted(p.keys()), ensure_ascii=False))

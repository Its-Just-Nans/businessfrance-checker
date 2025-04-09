# CHANGELOG

## Create a new version

```sh
rm -rf dist/ build/
python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install --upgrade build --break-system-packages
python3 -m build
python3 -m pip install --upgrade twine --break-system-packages
# create egg-info folder
python3 -m twine upload dist/* --verbose
# use __token__ auth
# enter token
```

## 2025-04-09

- Create package

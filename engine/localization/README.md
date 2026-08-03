# Zennity Engine Localization System

The `engine.localization` module is the single source of truth for UI translations in the Zennity Engine.
It uses a modular JSON-based approach with hot-reloading and robust fallback chains.

## How to use

In any engine module, import the `tr` function:
```python
from engine.localization import tr

print(tr("editor.toolbar.play"))
# Will output "Play" (en-US) or "Jogar" (pt-BR)
```

## Creating Translations

JSON files are stored in `locales/<lang-code>/`. They should be grouped by module:
`locales/en-US/editor.json`
`locales/en-US/graph.json`

## Plugins

If you are developing a plugin (e.g. `engine/plugins/myplugin`), simply create a `locales` directory inside it.
The `PluginManager` will automatically inject your translations into the global cache upon loading!

## Validating

Run the validator in your CI to ensure no missing keys:
```bash
python engine/localization/validator.py
```

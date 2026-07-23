
# ── Constantes de Eventos do Editor ──────────────────────────────────────────

# Tópicos de Seleção e Estrutura da Cena
EVENT_SELECTION_CHANGED = "editor.selection_changed"   # kwargs: obj (GameObject ou None)
EVENT_HIERARCHY_UPDATED = "editor.hierarchy_updated"   # kwargs: nulo
EVENT_PROPERTY_CHANGED  = "editor.property_changed"    # kwargs: component_name (str), prop_name (str), value (any)

# Tópicos de Recursos (Assets)
EVENT_ASSET_SELECTED    = "editor.asset_selected"      # kwargs: filepath (str)

# Tópicos de Simulação e Execução
EVENT_PLAY_STATE_CHANGED = "editor.play_state_changed"  # kwargs: state (str: 'play'/'pause'/'stop')

# Tópicos de Logs e Console
EVENT_LOG_ADDED         = "editor.log_added"           # kwargs: message (str), type (str: 'info'/'warning'/'error')

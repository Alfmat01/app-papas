# 🍽️ Alimentación para Papás

Aplicación familiar para Home Assistant, distribuida como integración personalizada compatible con HACS.

Nace del HTML **APP DE ALIMENTACIÓN PARA PAPÁS OCUPADOS** y conserva sus seis áreas principales: Hoy, Inicio, Plan 7 Días, Menú Semanal, Lista de Compra y Checklist Diario.

## Características

- Panel completo en la barra lateral de Home Assistant.
- Registro diario por fecha de desayuno, almuerzo, cena y notas.
- Menú semanal editable para Papá y Niñas.
- Plan guiado de 7 días.
- Lista de la compra con categorías y productos personalizados.
- Checklist diario con histórico por fecha.
- Puntuación diaria y promedio de los últimos 7 días.
- Persistencia centralizada mediante el almacenamiento de Home Assistant.
- Sin tokens ni URL de HA dentro del frontend.
- Responsive para móvil y escritorio.
- Modo claro, oscuro o automático.

## Instalación con HACS

1. En HACS, abre **Integraciones → ⋮ → Repositorios personalizados**.
2. Añade este repositorio como **Integration**.
3. Descarga **Alimentación para Papás**.
4. Reinicia Home Assistant.
5. Ve a **Ajustes → Dispositivos y servicios → Añadir integración**.
6. Busca **Alimentación para Papás** y finaliza la configuración.

HACS instala las integraciones en `custom_components/`, y este repositorio sigue la estructura de integración requerida por HACS.

## Instalación manual

Copia `custom_components/app_papas` dentro de tu directorio de configuración:

```text
/config/custom_components/app_papas/
```

Reinicia Home Assistant y añade la integración desde la interfaz.

## Uso

Tras configurar la integración aparecerá **Alimentación para Papás** en la barra lateral.

### Menú semanal

La aplicación parte del menú incluido en el HTML original. Puedes modificar cualquier comida y guardar automáticamente.

### Lista de compra

Los productos originales se incluyen como valores iniciales. Los productos que añadas quedan almacenados junto al resto de la aplicación.

### Datos diarios

Cada fecha tiene su propio registro. El checklist también es diario, por lo que ya no hace falta borrar manualmente las casillas para comenzar un nuevo día.

## Servicios

La integración incluye servicios pensados para automatizaciones futuras:

- `app_papas.reset_today`
- `app_papas.generate_shopping`

## Desarrollo

Estructura:

```text
custom_components/app_papas/
├── __init__.py
├── api.py
├── config_flow.py
├── const.py
├── defaults.py
├── frontend.py
├── manifest.json
├── services.yaml
├── storage.py
├── translations/
│   ├── en.json
│   └── es.json
└── frontend/
    └── app-papas.js
```

## Licencia

MIT. Ver `LICENSE`.

## Créditos

El contenido funcional y la organización inicial de la aplicación proceden del HTML suministrado para este proyecto.


## Antes de publicar

Sustituye `YOUR_GITHUB_USERNAME` en `custom_components/app_papas/manifest.json` por tu usuario de GitHub y crea el repositorio `app-papas` (o cambia las URLs por el nombre que elijas).

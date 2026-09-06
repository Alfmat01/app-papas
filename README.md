# App Papás para Home Assistant

Integración personalizada para Home Assistant, preparada para HACS, inspirada en el HTML original de Alimentación para Papás.

## Qué incluye

- Panel completo `Alimentación` en Home Assistant.
- Vista Inicio con resumen diario, racha, progreso y acciones rápidas.
- Vista Hoy con plan vs. lo realmente comido.
- Menú semanal editable para adulto y niños.
- Biblioteca de recetas completas con ingredientes, cantidades, tiempos y pasos.
- Asociación de recetas al menú para calcular automáticamente la compra.
- Lista de compra agrupada por categorías.
- Cantidades acumuladas para toda la familia (1 adulto + 1 ración por niño configurado).
- Detección orientativa de ingredientes en texto libre cuando no hay receta asociada.
- Checklist diario con histórico y racha.
- Plan de 7 días y comidas de emergencia.
- Sensores Home Assistant.
- Servicios de Home Assistant para automatizaciones.
- Tarjeta Lovelace `app-papas-card`.
- Persistencia en `.storage` de Home Assistant.

## Cantidades automáticas

Cuando una comida tiene una receta asociada, la aplicación toma los ingredientes de la receta y multiplica la cantidad por el número de raciones familiares configuradas.

Ejemplo: una receta indica 180 g de ternera por ración y hay 1 adulto + 1 niño:

`360 g · Ternera`

Si la misma receta se utiliza dos veces en la semana, la lista acumula:

`720 g · Ternera`

Cuando el texto del menú no tiene receta asociada, la aplicación intenta detectar ingredientes conocidos y aplica cantidades orientativas. Si escribes una cantidad explícita (`500 g de ternera`), esa cantidad tiene prioridad.

## Recetas

La pestaña `Recetas` contiene recetas base derivadas del menú original, con:

- ingredientes y cantidades
- categoría
- tiempo de preparación y cocción
- pasos de preparación
- alias para reconocimiento del texto

Desde cada receta se puede asignar directamente la receta a un día y comida del menú.

## Instalación HACS

Añade el repositorio como repositorio personalizado de tipo `Integration` en HACS y después instala `Alimentación para Papás`.

Repositorio:

`https://github.com/Alfmat01/app-papas`

## Desarrollo

La integración está en `custom_components/app_papas`.

Validaciones locales incluidas:

- compilación Python
- sintaxis JavaScript
- validación JSON
- tests de estructura, migración y generación de compra

## Servicios

- `app_papas.reset_today`
- `app_papas.generate_shopping`
- `app_papas.copy_week`
- `app_papas.add_shopping_item`
- `app_papas.complete_checklist`
- `app_papas.notify_today`
- `app_papas.set_menu_recipe`

## Tarjeta Lovelace

Después de instalar el recurso frontend, se puede añadir una tarjeta personalizada:

```yaml
type: custom:app-papas-card
```

## Nota

Las recetas incluidas son una base práctica para la aplicación y no sustituyen recomendaciones médicas o nutricionales personalizadas.

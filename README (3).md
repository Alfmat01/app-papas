# Alimentación para Papás

Integración HACS para Home Assistant basada en la aplicación original de alimentación para papás ocupados.

## Incluye

- Panel lateral completo para Home Assistant.
- Inicio con resumen del día, menú, progreso, racha y compra pendiente.
- Registro real de desayuno, almuerzo, cena y notas por fecha.
- Menú semanal editable para adulto y niños.
- Lista de compra por categorías con productos manuales y generación desde el menú.
- Checklist de 8 objetivos diarios con histórico de 14 días, media semanal y racha.
- Plan guiado de 7 días y tres comidas de emergencia reutilizables.
- Configuración del nombre del adulto, niños y notificaciones.
- Servicios de Home Assistant para reiniciar día, generar compra, copiar semana, añadir productos, completar checklist y enviar resumen.
- Sensores de Home Assistant para puntuación, compra pendiente, racha y próxima comida.
- Custom card opcional para Lovelace.
- Almacenamiento persistente de Home Assistant; no utiliza localStorage ni tokens en el frontend.

## Instalación

1. HACS → Integraciones → Repositorios personalizados.
2. Añade `https://github.com/Alfmat01/app-papas` como `Integration`.
3. Instala la integración y reinicia Home Assistant.
4. Configuración → Dispositivos y servicios → Añadir integración → **Alimentación para Papás**.

## Configuración

Puedes definir el nombre del adulto, nombres de niños y, opcionalmente, un servicio `notify.*` para la acción de resumen.

## Tarjeta Lovelace

El archivo está disponible en:

`/api/app_papas/static/app-papas-card.js`

Añádelo como recurso JavaScript de tipo `module` y usa:

```yaml
type: custom:app-papas-card
```

La documentación de Home Assistant mantiene el patrón de recursos para custom cards y de paneles personalizados para extensiones frontend. (https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/)

## Servicios

- `app_papas.reset_today`
- `app_papas.generate_shopping`
- `app_papas.copy_week`
- `app_papas.add_shopping_item`
- `app_papas.complete_checklist`
- `app_papas.notify_today`

## Autor

[@Alfmat01](https://github.com/Alfmat01)

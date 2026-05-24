# Computer Actions

Низкоуровневые действия для управления браузером напрямую через API. Используются для pixel-based (coordinate) взаимодействия вместо селекторов.

## Click

```python
response = client.computer_action.click(
    session_id,  # or session object
    x=500,
    y=300,
    button="left",        # "left" | "right" | "middle" | "back" | "forward" | "wheel"
    click_count=1,
    return_screenshot=False
)
print(response.success)
print(response.screenshot)  # base64 если requested
```

## Type Text

```python
response = client.computer_action.type_text(
    session_id,
    text="Hello, World!",
    return_screenshot=False
)
```

## Press Keys (xdotool format)

Key reference: https://github.com/sickcodes/xdotool-gui/blob/master/key_list.csv

```python
# Select all (Ctrl+A)
response = client.computer_action.press_keys(
    session_id,
    keys=["Control_L", "a"]
)

# Enter key
response = client.computer_action.press_keys(
    session_id,
    keys=["Return"]
)

# Copy (Ctrl+C)
response = client.computer_action.press_keys(
    session_id,
    keys=["Control_L", "c"]
)

# Paste (Ctrl+V)
response = client.computer_action.press_keys(
    session_id,
    keys=["Control_L", "v"]
)

# Alt+Tab
response = client.computer_action.press_keys(
    session_id,
    keys=["Alt_L", "Tab"]
)
```

## Move Mouse

```python
response = client.computer_action.move_mouse(
    session_id,
    x=500,
    y=300,
    return_screenshot=False
)
```

## Drag

```python
response = client.computer_action.drag(
    session_id,
    coordinates=[
        {"x": 100, "y": 100},
        {"x": 200, "y": 200},
        {"x": 300, "y": 300}
    ],
    return_screenshot=False
)
```

## Scroll

```python
response = client.computer_action.scroll(
    session_id,
    x=500,
    y=300,
    scroll_x=0,
    scroll_y=100,    # Positive = scroll down
    return_screenshot=False
)
```

## Screenshot Only

```python
response = client.computer_action.screenshot(session_id)
print(response.screenshot)  # base64 string
```

## Key Coordinates

- All coordinates are relative to the screen/viewport
- Default screen: 1280x720 (configurable)
- Origin (0,0) is top-left corner
- Coordinates use full pixel values
- For precision clicking, ensure screen dimensions match session config

## 3DHunyuan Use Cases

- **Upload button clicks**: When file input selectors are hidden, use computer actions to click visible upload areas
- **Generation button**: Click `knopka_generate` via coordinates if XPath selectors become unreliable
- **Photo preview interaction**: Click on preview thumbnails using coordinates

## Important Notes

- `session_id` can be a string or the session object itself (recommended)
- All computer actions require an active session
- Screenshot responses return base64-encoded images
- Use `return_screenshot=True` sparingly to save bandwidth
- Computer actions are useful for AI agents and low-level interaction

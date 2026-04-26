# RoborukaAPI – dokumentace knihovny

## Přehled

`RoborukaAPI` je Python knihovna pro ovládání robotické ruky přes sériový port. 

Kód pro knihovnu je ve složce [/code/API/](../code/API/) pro využití ve vlastním projektu doporučuji zkopírovat odtud a vytvořit is virtuální prostředí (venv)

Součástí knihovny je také Flask webový server s webovým rozhraním.

------

## Instalace závislostí

```bash
pip install -r requirements.txt
```

------

## Třída `roboruka`

### Konstruktor

```python
roboruka(port: str)
```

Otevře sériové spojení s robotem.

| Parametr | Typ   | Popis                                         |
| -------- | ----- | --------------------------------------------- |
| `port`   | `str` | Cesta k sériovému portu, např. `/dev/ttyACM0` |

**Výjimky:**

- `Exception` – pokud nelze port otevřít pro zápis

**Příklad:**

```python
from RoborukaAPI import roboruka
robot = roboruka("/dev/ttyACM0")
```

------

### Metody

#### `get_angles() → list[float]`

Vrátí kopii aktuálně nastavených úhlů všech 6 serv.

```python
angles = robot.get_angles()
# → [0, -90, 0, 0, 0, 0]
```

------

#### `set_angles(angles: list[float])`

Nastaví úhly všech 6 serv a odešle příkazy do hardwaru.

| Parametr | Typ           | Popis                                      |
| -------- | ------------- | ------------------------------------------ |
| `angles` | `list[float]` | Seznam 6 úhlů v rozsahu `[-90, 90]` stupňů |

**Výjimky:**

- `ValueError` – pokud seznam nemá 6 prvků, obsahuje nečíselné hodnoty nebo jsou úhly mimo rozsah

**Příklad:**

```python
robot.set_angles([0, -45, 30, 0, 0, 0])
```

Každý úhel je interně přemapován z rozsahu `[-90, 90]` na `[0, 1024]` a odeslán jako textový příkaz ve formátu `S{n}:{hodnota}\n`.

------

#### `send_command(command: str)`

Odešle libovolný textový příkaz přes sériový port (UTF-8).

```python
robot.send_command("S1:0512\n")
```

------

#### `close()`

Odešle příkaz `stop`, zavře sériový port.

```python
robot.close()
```

------

## Funkce `solve_ik`

```python
solve_ik(user_x, user_y, user_z, theta_deg) → dict | None
```

Řeší inverzní kinematiku (IK) pro 6-osé rameno.

**Tato Funkce je stále ve vývoji a není perfektní!**

### Geometrie ruky

výchozí naměřená geometrie ruky, může být jiná na jiných modelech

| Parametr                          | Hodnota    |
| --------------------------------- | ---------- |
| Výška ramene (shoulder)           | 0.75       |
| Délka článku L1 (rameno → loket)  | 1.05       |
| Délka článku L2 (loket → zápěstí) | 1.00       |
| Offset gripperu od zápěstí        | [0.2, 0.9] |

### Souřadnicová konvence

Uživatelský souřadnicový systém se mapuje na interní Three.js systém:

| Uživatel | Three.js | Význam        |
| -------- | -------- | ------------- |
| X        | Z        | dopředu/dozadu|
| Y        | X        | do stran      |
| Z        | Y        | nahoru/dolů   |

### Parametry

| Parametr    | Typ     | Popis                                                 |
| ----------- | ------- | ----------------------------------------------------- |
| `user_x`    | `float` | Cíl ve směru dopředu                                  |
| `user_y`    | `float` | Cíl ve směru do strany (musí být ≥ 0)                 |
| `user_z`    | `float` | Výška cíle                                            |
| `theta_deg` | `float` | Požadovaný celkový úhel ramene (p1+p2+p3) ve stupních |

### Návratová hodnota

Vrací `dict` s klíči:

| Klíč        | Typ     | Popis                    |
| ----------- | ------- | ------------------------ |
| `reachable` | `bool`  | Zda je bod dosažitelný   |
| `yaw`       | `float` | Rotace základny (stupně) |
| `pitch1`    | `float` | Úhel ramene (stupně)     |
| `pitch2`    | `float` | Úhel lokte (stupně)      |
| `pitch3`    | `float` | Úhel zápěstí (stupně)    |

Vrací `None`, pokud je cíl příliš blízko (singularita).

Všechny úhly jsou oříznuty do rozsahu `[-90, 90]` stupňů.

**Příklad:**

```python
from RoborukaAPI import solve_ik

result = solve_ik(1.0, 0.0, 1.0, theta_deg=30)
if result is None:
    print("Singularita – cíl příliš blízko")
elif result['reachable']:
    print("Dosažitelný:", result)
else:
    print("Nedosažitelný (arm natažen):", result)
```

------

## Webový server (`__main__.py`)

Server se spustí automaticky na portu `5000`. Pokud není nalezen žádný sériový port `/dev/ttyACM*`, spustí se v simulačním režimu.

### Endpointy

#### `GET /`

Přesměruje na `/fk`.

#### `GET /fk`

Vrátí FK (Forward Kinematics) webové rozhraní.

#### `GET /ik`

Vrátí IK (Inverse Kinematics) webové rozhraní.

------

#### `GET /get_angles`

Vrátí aktuální úhly serv.

**Odpověď:**

```json
{ "angles": [0, -90, 0, 0, 0, 0] }
```

------

#### `POST /set_angles`

Nastaví úhly serv přímo.

**Tělo požadavku:**

```json
{ "angles": [0, -45, 30, 0, 0, 0] }
```

**Odpověď (úspěch):**

```json
{ "status": "ok" }
```

------

#### `POST /solve_ik`

Vypočítá IK a volitelně odešle výsledek do robota.

**Tělo požadavku:**

| Pole      | Typ   | Povinné | Výchozí | Popis                       |
| --------- | ----- | ------- | ------- | --------------------------- |
| `x`       | float | ✓       | –       | Cíl X (dopředu)             |
| `y`       | float | ✓       | –       | Cíl Y (do strany, ≥ 0)      |
| `z`       | float | ✓       | –       | Cíl Z (výška)               |
| `theta`   | float | ✓       | –       | Celkový úhel ramene         |
| `roll`    | float |         | 0       | Rotace zápěstí              |
| `gripper` | float |         | 0       | Otevření gripperu (0–100 %) |

**Odpověď (úspěch):**

```json
{
  "reachable": true,
  "yaw": 0.0,
  "pitch1": -12.5,
  "pitch2": 45.0,
  "pitch3": -2.5,
  "roll": 0.0,
  "gripper": 50.0
}
```

**Chybové stavové kódy:**

| Kód   | Popis                                            |
| ----- | ------------------------------------------------ |
| `400` | Chybný požadavek (neplatné parametry nebo Y < 0) |
| `422` | Singularita – cíl příliš blízko                  |
| `500` | Robot není připojen                              |

------

## Demonstrační program

`ds_controller.py` je program pro ovládání robotické ruky pomocí dual sense 5 ovladače (ovladače k PS5), ovladač musí být připojený buď přes usb nebo bluetooth a ruka přes usb.
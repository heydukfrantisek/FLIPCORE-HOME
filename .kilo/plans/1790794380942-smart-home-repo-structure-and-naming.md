# FLIPCORE-HOME — struktura repozitáře, standard názvů a prompt pro generování

## 1. Kontext

Repozitář je prázdný (jediný `README.md`: „FLIPCORE-HOME / FLIPCORE HOMEASISTENT"). Cílem je založit
repozitář pro Home Assistant, který slouží jako **zdroj pravdy v Git** — konfigurace, firmware,
dokumentace i CI validace názvů entit.

### Rozhodnutí (potvrzena uživatelem)

| Oblast | Rozhodnutí |
|---|---|
| Předmět | Home Assistant konfigurační repozitář |
| Obsah | HA konfigurace + ESPHome + Docker/MQTT/Zigbee + dokumentace |
| Zdroj pravdy pro entity_id | YAML (packages / ESPHome), ne HA UI |
| Jazyk názvů | `entity_id` a device name anglicky, aliasy/popisy pro UI česky |
| Naming konvence | HA / AndreZ paranormální (`location_device_function_measurement`) |
| Jazyk dokumentace a promptu | Čeština (komentáře v YAML anglicky) |
| Instalace | Home Assistant OS / Supervised, config adresář = repo |
| Výstupy | Prompt + dokumentace + CI validátor |
| Místnosti | Vzorový seznam, prompt parametrizovatelný |
| CI | GitHub Actions |

## 2. Struktura repozitáře

```
flipcore-home/
├── configuration.yaml            # kořen: jen !include a řídké top-level klíče
├── packages/
│   ├── core/                     # logger, defaults, http, tts, person, sun
│   ├── areas/                    # area/label registry (registr místností)
│   ├── devices/                  # <device_slug>.yaml — definice zařízení
│   │   ├── lights/  switches/  sensors/  climate/  covers/  media/
│   │   └── binary_sensors/  locks/  vacuum/  fans/  water/  energy/
│   ├── integrations/             # mqtt, zigbee2mqtt, esphome, ota, cloud_* ...
│   ├── groups/                   # skupiny jako view: (Light groups, ...)
│   ├── views/                    # view: definice pro UI
│   ├── dashboards/               # lovelace yaml (vložené do HA přes storage_mode: yaml)
│   ├── automations/              # <domain>_<filename>.yaml, 1 top-level klíč na soubor
│   ├── scripts/                  # <domain>_<action>.yaml
│   ├── scenes/                   # <domain>_<filename>.yaml
│   └── customize/                # legacy, jen pro entity bez vlastního balíčku
├── esphome/
│   ├── common/                   # packages s wifi/api/logging/ota
│   ├── nodes/                    # <device_slug>.yaml
│   └── dashboards/
├── docker/
│   ├── docker-compose.yml        # mosquitto, z2m, zwave-js-ui
│   ├── mosquitto/{mosquitto.conf,conf.d/,acl}
│   └── zigbee2mqtt/
├── blueprints/
│   ├── automation/  script/
├── docs/
│   ├── naming.md                 # standard názvů (česky)
│   ├── structure.md              # pravidla ukládání a !include
│   ├── devices/                  # jedna stránka na zařízení
│   ├── network.md, backup.md
│   └── prompts/
│       └── naming.md             # ← copy-paste prompt pro AI
├── scripts/
│   └── validate_entity_ids.py    # CI validátor
├── tests/
│   └── fixtures/                 # vzorové YAML pro testy validátoru
├── .github/workflows/validate.yml
├── secrets.yaml.example
├── .gitignore, .editorconfig, .yamllint.yml, pyproject.toml
└── README.md
```

Pravidla pro `configuration.yaml`:
- neobsahuje žádné entity přímo, jen `default_config:`, `homeassistant: packages: !include_dir_merge_named packages`,
  `automation: !include_dir_merge_list packages/automations`, `script:`/`scene:` obdobně;
- `secrets.yaml` je v `.gitignore`, v repo je jen `secrets.yaml.example`.

## 3. Standard názvů (`docs/naming.md`)

### entity_id
Vzor: `domain.location_device_function[_measurement]`

- Pořadí segmentů vždy: **místnost → zařízení → funkce → měření**.
- Vše anglicky, `snake_case`, bez diakritiky a bez háčků.
- Nepoužívat `_id`, `_sensor`, `_switch` jako redundantní přípony.
- Čísla oddělovat podtržítkem: `light.office_ceiling_light_2`.
- Binární stavy: `_on` / `_off` (`switch.garden_pump_on`), otevřenost `_open` / `_closed`.
- Číselné entity **vždy** s jednotkou: `sensor.living_room_temperature`, `sensor.kitchen_humidity`.
  Jednotka je součást názvu i jako `unit_of_measurement`; entity bez měřicí funkce jednotku nemá.
- Bez časových/sekvenčních údajů (`_1`, `_2` jen pokud je v místnosti skutečně více stejných zařízení).
- Kombinovaný senzor (`temp_humidity`) → dvě entity, ne jedna s oběma hodnotami.

### device name / alias
- `device name` (viditelný v UI a v Device registry) anglicky ve stejném vzoru jako `entity_id` bez
  domény a bez měření: `Kitchen Ceiling Light`.
- `friendly_name` (alias) **česky** a přirozeně: `Kuchyň – stropní světlo`.
- Stejný alias musí být na všech entitách jednoho zařízení s výjimkou měřicích entit, které mají
  jednotku v názvu (`Kuchyň – stropní světlo`, `Teplota v kuchyni`).

### Příklady (vzorová sada místností)

| Doména | entity_id | alias |
|---|---|---|
| light | `light.kitchen_ceiling_light` | Kuchyň – stropní světlo |
| light | `light.living_room_tv_backlight` | Obývací pokoj – podsvícení TV |
| switch | `switch.garden_pump_on` | Zahrada – zavlažovací čerpadlo |
| sensor | `sensor.living_room_temperature` | Teplota v obývacím pokoji |
| sensor | `sensor.outdoor_humidity` | Vlhkost venku |
| binary_sensor | `binary_sensor.hallway_motion` | Chodba – pohyb |
| cover | `cover.bedroom_blind` | Ložnice – žaluzie |
| climate | `climate.bedroom_thermostat` | Ložnice – termostat |
| lock | `lock.front_door` | Vstupní dveře – zámek |
| number | `number.bedroom_humidity_setpoint` | Ložnice – nastavená vlhkost |
| select | `select.living_room_scene` | Obývací pokoj – scéna |

Předpony domén: `sensor`, `binary_sensor`, `switch`, `light`, `cover`, `climate`, `lock`, `number`,
`select`, `button`, `scene`, `script`, `automation`, `input_*`, `counter`, `timer`, `update`, `vacuum`,
`water_heater`, `fan`, `media_player`, `image`, `camera`, `calendar`, `todo`, `device_tracker`.

## 4. Prompt (`docs/prompts/naming.md`)

Toto je hlavní požadovaný výstup — hotový prompt do kopírování:

```text
Jsi expert na Home Assistant. Z údajů níže vygeneruj tabulku entit pro můj
Home Assistant config repozitář.

VSTUP
- Místnosti: {{seznam_místností_oddělený_čárkou}}
- Zařízení: {{seznam zařízení ve tvaru "místnost | typ zařízení | popis/model | extra funkce"}}
- Jazyk aliasů: čeština
- Jazyk entity_id a device name: angličtina

PRAVIDLA (dodržuj přesně)
1. entity_id má tvar domain.location_device_function[_measurement].
   Pořadí segmentů je vždy místnost → zařízení → funkce → měření.
2. Vše anglicky, snake_case, bez diakritiky a bez čárlíček. entity_id je malými písmeny.
3. Nepoužívej přípony _id, _sensor, _switch ani jiné nadbytečné označení typu.
4. Číselné entity musejí mít jednotku v názvu (temperature, humidity, power, energy, voltage,
   current, pressure, co2, pm25, illuminance, battery, speed, duration, …).
   Entita bez měřicí funkce jednotku v názvu nemá.
5. Binární stavy končí _on/_off; otevřenost _open/_closed; stav připojení _connected/_disconnected.
6. Čísla odděluj podtržítkem: light.office_ceiling_light_2.
7. Kombinovaný senzor (teplota+vlhkost) rozdej na dvě entity, nikdy ne jednu s oběma hodnotami.
8. Jedno zařízení = jeden device name ve tvaru "Kitchen Ceiling Light" (PascalCase, bez měření).
9. Aliasy jsou česky a přirozeně: "Kuchyň – stropní světlo", "Teplota v kuchyni",
   "Vlhkost venku". Použij typografickou pomlčku –.
10. Alias je na všech entitách zařízení stejný; měřicí entity mají v aliasu jednotku
    nebo měřenou veličinu.
11. Nedoporučuj nové entity, pokud už pro danou funkci existuje vestavěný sensor
    nebo device_class (např. teplota → sensor, ne číselná input_number).
12. U zařízení s napájením přidej i binární senzor napájení, pokud jej integrace poskytuje.

VÝSTUP
Přes dvě tabulky:

A) entity_id | alias | device name | domain | device_class | jednotka | typ (primární/podřízený)
B) Pro každé zařízení: jednořádkový YAML blok připravený do packages/devices/<device_slug>.yaml

POTOM
- Seznam všech entit, které jsi přejmenoval oproti výchozímu názvu integace, a doplň řádek
  s legacy alias (entity_id před přejmenováním), aby historie v grafu nezůstala přerušená.
- U každého zařízení uveď doporučený device_slug a zda patří do packages/devices/
  nebo do esphome/nodes/.
- Odděl sekci "POZOR" s chybami a nejasnostmi ve vstupu.

NEPOŽADUJ SI DALŠÍ DOTAZY — pokud něco chybí, odhadni to podle pravidel
a uveď to v sekci POZOR.
```

## 5. Validátor (`scripts/validate_entity_ids.py`)

Bez externích závislostí, jen stdlib (`pathlib`, `re`, `yaml` z PyYAML — pokud není, použít
`ruamel` nebo regex fallback; doporučeno: `PyYAML` jako jediná závislost v `pyproject.toml`).

Kontroluje ve všech `packages/**/*.yaml`, `esphome/**/*.yaml`, `blueprints/**/*.yaml`:

1. `entity_id` odpovídá `^(light|switch|sensor|binary_sensor|cover|climate|lock|number|select|fan|media_player|scene|script|automation|button|vacuum|counter|timer|update|input_[a-z_]+)\.[a-z0-9_]+$` — žádné háčky, čárky, velká písmena.
2. Pořadí segmentů: první segment je v seznamu známých místností z `packages/areas/areas.yaml`.
3. Duplikáty entity_id v rámci repozitáře.
4. Číselné entity (stateClass measurement, nebo konfigurace sensoru s `unit_of_measurement`)
   mají v názvu jednotku ze seznamu známých jednotek.
5. Binární entity nekončí `_on`/`_off` ani jiným nepodporovaným suffixem.
6. Zakázané přípony `_id`, `_sensor`, `_switch`, `_entity`.
7. Soubor v `packages/automations/` obsahuje právě jeden top-level klíč `alias:` ve tvaru
   `<Zařízení> <akce> [trigger]` a jeden příslušný klíč (`trigger`/`action`/`condition`).
8. Každý soubor v `packages/devices/` má hlavičku s `id:` a `name:`.

Výstup: `path:line: entity_id — důvod`, exit code 1 při chybách, `--fix` jako rezerva (NEimplementovat
v první verzi).

Testy: `tests/test_validate_entity_ids.py` s fixtures — platný soubor, každá chyba jeden fixture.

## 6. GitHub Actions

`.github/workflows/validate.yml`:
- trigger: `push` na `main`, `pull_request`;
- kroky: checkout → `setup-python@v5` (3.12) → `pip install -e .[dev]` → `yamllint -c .yamllint.yml .`
  → `pytest` → `python scripts/validate_entity_ids.py`;
- `.yamllint.yml`: pravidla HA, ignorovat `line-length` warning pro `esphome/`.

## 7. Implementační kroky

1. `.gitignore` (secrets.yaml, `.storage/`, `__pycache__`), `.editorconfig`, `.yamllint.yml`,
   `pyproject.toml` s `[project]` + `[tool.pytest.ini_options]`.
2. `configuration.yaml` s `!include_dir_merge_named` / `!include_dir_merge_list`.
3. Prázdné adresáře s `.gitkeep` nebo `README.md` placeholder podle struktury z §2.
4. `packages/areas/areas.yaml` — vzorový seznam místností s `id`, `name` (CZ), `aliases`.
5. `packages/devices/lights/kitchen_ceiling_light.yaml` jako referenční příklad (1 zařízení, všechny entity s `unique_id`, `device_class`, `unit_of_measurement` kde relevantní).
6. `docs/naming.md` (§3) a `docs/structure.md` (pravidla `!include`, kdy `packages:` vs `automation:`).
7. `docs/prompts/naming.md` (§4) — doslova text z §4.
8. `scripts/validate_entity_ids.py` + `tests/`.
9. `.github/workflows/validate.yml`.
10. `secrets.yaml.example`, `README.md` s popisem repozitáře a bootstrap krokem (klonout do
    `/config` na HA OS serveru).

## 8. Validace

- `yamllint .` bez chyb.
- `pytest` — zelené fixture testy i pro fixtures s chybami.
- `python scripts/validate_entity_ids.py` projde na referenčním zařízení z kroku 5.
- Ruční smoke test: na HA serveru naklonovat repo do `/config`, restartovat, ověřit
  viditelnost entit `kitchen_ceiling_light` a správné aliasy v UI.

## 9. Mimo rozsah / rizika

- **Migrace existujících entit**: pokud už v HA existují entity s jinými `entity_id`, plán
  neobsahuje migrační skript. Řešit přes `homeassistant.customize` aliasy nebo ručně;
  samostatný bod pro pozdější `entity_id:` přejmenování po migraci na UI-free YAML.
- **Dashboardy**: Lovelace YAML verze se mění rychle; `storage_mode: yaml` bude v kroku 3
  jen jako prázdná kostra, konkrétní dashboardy mimo rozsah.
- **CI validátor nezachytí** duplicitu proti běžící instanci HA (jen v rámci repozitáře).
- Prompty v `docs/prompts/naming.md` jsou české a předpokládají, že se použijí v českém
  jazyce modelu.

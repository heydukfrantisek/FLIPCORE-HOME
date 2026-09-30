# Plán: šablona repozitáře Proxmox + HAOS + ESPHome

## Cíl

Vytvořit **kompletní šablonový repozitář** pro domácí infrastrukturu:
Proxmox host (předpokládáme již nainstalovaný) → virtuální stroj **Home Assistant OS** spravovaný
Terraformem → **ESPHome** konfigurace jako doplněk. Struktura musí být přenositelná do jiných projektů
(klon repozitáře + přepis parametrů).

## Rozhodnutí (shodnuto s uživatelem)

| Oblast | Rozhodnutí |
|---|---|
| Účel repozitáře | Kompletní šablona s obsahem, ne jen prázdná kostra |
| Tvorba VM | Terraform (provider `bpg/proxmox`) |
| Hostitel PVE | Mimo scope — předpokládáme běžící Proxmox VE |
| Reuse | Klon repozitáře + `terraform.tfvars`, žádné placeholder tokeny |
| ESPHome | `packages/` + `devices/` + `secrets.yaml` (v .gitignore) |
| Konfigurace HA | Jen dokumentace kroků v `docs/`, žádný provisioning |
| Disk VM | `local-lvm` + `import_qcow2` z oficiálního `haos.qcow2` |
| Síť/IP | Ruční MAC v TF, DHCP rezervace na routeru (popsaná v README) |
| Tajné údaje | `.gitignore` + `*.example` šablony (bez SOPS) |

## Cílová struktura

```
.
├── README.md                      # co to je, rychlý start, odkaz na docs
├── .gitignore
├── .editorconfig
├── Makefile                       # tf init/plan/apply, esphome compile/run, backup
├── terraform/
│   ├── versions.tf                # pin providera bpg/proxmox + required_version
│   ├── providers.tf               # auth z proměnných prostředí (PVE_TOKEN_ID/SECRET)
│   ├── variables.tf               # parametry s popisky, defaults a validací
│   ├── main.tf                    # VM + import disku + síť + UEFI
│   ├── outputs.tf                 # vm_id, vm_name, mac_address, console hint
│   ├── terraform.tfvars.example   # šablona hodnot pro nový projekt
│   └── README.md                  # požadovaná práva PVE API tokenu
├── scripts/
│   ├── bootstrap.sh               # kontrola PVE, stažení haos.qcow2, příprava images/
│   ├── update-haos.sh             # stažení nové verze + zápis haos-version.txt
│   └── backup-haos.sh             # volitelný snapshot/vzdálená záloha přes PVE API
├── docs/
│   ├── 00-proxmox-prereq.md
│   ├── 01-create-vm.md
│   ├── 02-haos-first-boot.md
│   ├── 03-haos-integrations.md
│   ├── 04-backups.md
│   ├── 05-network.md
│   └── 06-new-project.md          # klon šablony do dalšího projektu
├── esphome/
│   ├── README.md
│   ├── esphome.yaml               # kořenový soubor, packages: base + devices
│   ├── secrets.yaml.example
│   ├── packages/
│   │   ├── base.yaml               # wifi, api, logger, ota, web_server
│   │   ├── network-static.yaml     # volitelná statická IP (výchozí stav zakomentovaný)
│   │   ├── api-ha.yaml             # API, unique_id, device_class pro HA
│   │   └── mqtt.yaml               # volitelný MQTT balíček
│   ├── devices/
│   │   └── example-sensor.yaml     # referenční ESP32 + DHT22 + relé
│   └── shared/                     # helpery pro senzory/světla
└── haos/
    ├── README.md
    ├── image/                      # stažený haos.qcow2 (gitignore)
    └── dashboards/                 # ukázkové Lovelace dashboardy
```

## Klíčová implementace

### Terraform

- Provider `bpg/proxmox` (~> 0.68), auth z `PVE_URL`, `PVE_TOKEN_ID`, `PVE_TOKEN_SECRET`
  z prostředí, s jasnou hláškou, pokud chybí.
- Proměnné v `variables.tf`: `project_name`, `vm_name`, `node_name`, `haos_version`,
  `vm_cores`, `vm_memory_mb`, `vm_disk_gb`, `vm_disk_storage` (default `local-lvm`),
  `network_bridge` (default `vmbr0`), `network_mac` (validace MAC formátu), `haos_qcow2_url`,
  `haos_image_path`.
- Disk: `null_resource` + `local-exec` stáhne `haos.qcow2` dle `haos-version.txt` a spustí
  `qm importdisk <vmid> <image> <storage> --format qcow2`; import je idempotentní (guard na
  existující volume). Po importu `qm set <vmid> --scsihw virtio-scsi-pci --boot order=scsi0`.
  **Pořadí je kritické**: import disku → create VM prázdného disku (aby se disky nevršily).
- VM: UEFI (`efidisk0` datastore_id + type `4m`), `agent { enabled = true }`,
  serial console pro přihlášení k HAOS, `network_device` s ručně zadanou MAC.
- Outputs: `vm_id`, `vm_name`, `mac_address` (pro DHCP rezervaci).

### `.gitignore`

`*.tfvars`, `*.tfstate*`, `.terraform/`, `terraform.lock.hcl` volitelně (předpoklad: commitovat),
`images/`, `*.qcow2`, `haos/image/`, `esphome/secrets.yaml`, `.env`.

### ESPHome

- `esphome.yaml` jako kořen, `packages:` → `packages/base.yaml` + `devices/*.yaml`.
- `packages/base.yaml`: `wifi`, `api`, `logger`, `ota`, `web_server`, hodnoty z `secrets.yaml`
  (`wifi_ssid`, `wifi_password`).
- `packages/api-ha.yaml`: `api:` s `encryption` klíčem z `secrets.yaml`; každé zařízení má
  `friendly_name`, `name_add_mac_suffix: false` a jednoznačné `unique_id` (prevence duplicit v HA).
- `devices/example-sensor.yaml`: ESP32 + DHT22 + relé, s komentářem „zkopíruj a uprav".
- `secrets.yaml.example`: `wifi_ssid`, `wifi_password`, `api_encryption_key` (generovat
  `openssl rand -base64 32`), `mqtt_password`.

### Skripty

Všechny s `set -euo pipefail`, bez logování hesel.

- `bootstrap.sh` — ověří `qm`/`pveversion`, načte hodnoty z `terraform.tfvars`, připraví
  `images/`, zkontroluje dostupnost API, spustí `terraform init`.
- `update-haos.sh` — stáhne `haos_*.qcow2.xz` pro zadanou verzi, rozbalí, zapíše `haos-version.txt`,
  vypíše instrukci pro `terraform apply -replace=terraform_data.image`.
- `backup-haos.sh` — volitelný snapshot přes PVE API token; jasně popíše omezení oproti
  PVE Backup Server.

### Makefile

`make init|plan|apply|destroy|image|esphome-validate|esphome-compile|esphome-run DEV=<name>|backup`.

### Dokumentace

`docs/` česky, krok za krokem, s očekávaným výstupem každého kroku a odkazy na oficiální
dokumentaci PVE/HAOS. `docs/06-new-project.md` popíše klon šablony a co přepsat
(`project_name`, `vm_name`, `node_name`, `network_mac`, síť, nový ESPHome device).

## Kroky implementace

1. `.gitignore`, `.editorconfig`, hlavní `README.md`.
2. `terraform/` — versions, providers, variables, main, outputs, `terraform.tfvars.example`, README
   s právy PVE API tokenu (`VM.Audit`, `VM.PowerMgmt`, `VM.Allocate`, `VM.Clone`,
   `VM.Config.Disk`, `Datastore.AllocateSpace`, `Sys.Audit`).
3. `scripts/` (bootstrap, update-haos, backup) + `haos/README.md` + `haos/dashboards/`.
4. `esphome/` — kořenový yaml, packages, referenční zařízení, `secrets.yaml.example`.
5. `docs/` (7 souborů) + `Makefile`.
6. Validace.

## Validace

- `terraform fmt -recursive -check`
- `terraform -chdir=terraform validate` (bez připojení k PVE; `plan`/`apply` vyžadují PVE)
- `bash -n scripts/*.sh` (+ `shellcheck`, pokud dostupný)
- `esphome config esphome/esphome.yaml` (pokud je ESPHome nainstalováno; jinak přeskočit
  a uvést v README)

Pokud v prostředí není PVE ani ESPHome, validace se omezí na formátování, parsování HCL a
syntaxovou kontrolu shellu — to se zaznamená v výsledku.

## Rizika

- `qm importdisk` + UEFI je nejcitlivější část; při chybě importu se VM vytvoří bez bootovatelného
  disku. Řešení: `depends_on` řetězec (image → import → VM) a `fileexists`/grep guard pro idempotenci.
- API provideru `bpg/proxmox` se mezi verzemi mění → pin v `versions.tf`, poznámka v `docs/`.
- `terraform plan` bez platného PVE tokenu selže — bootstrap skript musí hlásit chybě s instrukcí.

## Otevřené otázky

Žádné blokující. Volitelně později: plná MQTT broker addon konfigurace (aktuálně jen volitelný
`packages/mqtt.yaml`), dashboardy pro konkrétní zařízení.
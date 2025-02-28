# IBM MQ Monitoring – README

## 📌 IBM MQ – Klíčové pojmy a architektura

https://www.youtube.com/watch?v=ynjc5GMQeRA

### 🔹 Základní pojmy
- **Queue Manager (QM)** – hlavní součást IBM MQ, spravuje a zpracovává zprávy v různých frontách.
- **Queue (Fronta)** – místo, kam aplikace posílají a odkud přijímají zprávy.
- **Channel (Kanál)** – komunikační cesta mezi dvěma systémy nebo queue managery.
- **Message (Zpráva)** – data přenášená mezi aplikacemi pomocí IBM MQ.
- **Listener (Posluchač)** – proces, který čeká na spojení a přijímá zprávy.

### 🔹 Jak to funguje?
1. Aplikace 1 pošle zprávu do fronty (`PUT`).
2. IBM MQ zprávu uchová v **queue manageru**.
3. Aplikace 2 si zprávu vyzvedne (`GET`).
4. Pokud příjemce neexistuje, zpráva může čekat až do jeho spuštění.

> 📌 **Výhoda IBM MQ:** Pokud příjemce neběží, zpráva se neztratí (pokud je persistentní).

---

## 🔹 Jak se naše DEMO liší od produkce?

| **Funkce**             | **Naše DEMO (Docker)** | **Produkční IBM MQ** |
|-----------------------|----------------------|---------------------|
| **Queue Manager**     | `QM1` (jeden)        | Více QM pro HA     |
| **Uživatelé & Role**  | `admin/passw0rd`     | LDAP, Kerberos, RBAC |
| **Zabezpečení (TLS)** | ❌ Neaktivní         | ✅ Povinné šifrování |
| **Trvalé zprávy**     | ❌ Volitelné         | ✅ Nutné pro HA |
| **Monitoring**        | ❌ Ruční dotazy      | ✅ IBM Monitoring |

> 👉 **Chceš přidat bezpečnost a autentizaci do testovacího prostředí?** To bychom museli přidat TLS a správu uživatelů.

---

## 🔹 Co je součástí našeho testovacího prostředí?
- ✔ **Queue Manager:** `QM1` (spravuje fronty)
- ✔ **Dvě testovací fronty:** `DEV.QUEUE.1`, `DEV.QUEUE.2`
- ✔ **Možnost posílat zprávy pomocí Pythonu**
- ✔ **CLI příkazy pro kontrolu front**
- ✔ **Automatické posílání zpráv (simulace trafficu)**

---

## ❌ Co chybí oproti produkci?
- ❌ **TLS zabezpečení** (můžeme přidat, pokud chceš)
- ❌ **Víc queue managerů pro HA**
- ❌ **Alerty a logování**

> 👉 **Chceš to rozšířit o bezpečnost a monitoring? Dej vědět! 🚀**

## Instalace IBM MQ Clienta

Tento návod popisuje instalaci IBM MQ Clienta a knihovny `pymqi` pro monitorování IBM MQ.

https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/

### 1. Nastavení proměnných prostředí

Nejprve nastavíme potřebné proměnné prostředí:

```bash
export MQ_INSTALLATION_PATH="/home/pesourob/mq-client"
export PATH="$MQ_INSTALLATION_PATH/bin:$PATH"
export LD_LIBRARY_PATH="$MQ_INSTALLATION_PATH/lib64:$LD_LIBRARY_PATH"
export PYTHONPATH="$MQ_INSTALLATION_PATH/lib64:$PYTHONPATH"
```

Načtení nového profilu:

```bash
source ~/.bashrc  # nebo source ~/.bash_profile
```

Ověření správného nastavení:

```bash
echo $MQ_INSTALLATION_PATH
```
**Výstup:**
```
/home/pesourob/mq-client
```

### 2. Ověření instalace IBM MQ Clienta

Spusť příkaz:

```bash
dspmqver
```

**Očekávaný výstup:**
```
Name:        IBM MQ
Version:     9.4.1.1
Level:       p941-001-241129
BuildType:   IKAP - (Production)
Platform:    IBM MQ for Linux (x86-64 platform)
Mode:        64-bit
O/S:         Linux 5.14.0-503.26.1.el9_5.x86_64
O/S Details: Rocky Linux 9.5 (Blue Onyx)
InstName:    MQNI94L24112900P
InstDesc:    IBM MQ V9.4.1.1 (Redistributable)
Primary:     N/A
InstPath:    /home/pesourob/mq-client
DataPath:    /home/pesourob/IBM/MQ/data
MaxCmdLevel: 941
LicenseType: License not accepted
ReleaseType: Continuous Delivery (CD)
```

### 3. Instalace `pymqi`

Jakmile je IBM MQ Client správně nastaven, můžeme nainstalovat knihovnu `pymqi`:

```bash
pip3 install pymqi
```

**Očekávaný výstup:**
```
Defaulting to user installation because normal site-packages is not writeable
Collecting pymqi
Downloading pymqi-1.12.11.tar.gz (91 kB)
|████████████████████████████████| 91 kB 2.7 MB/s
Installing build dependencies ... done
Getting requirements to build wheel ... done
Preparing metadata (pyproject.toml) ... done
Building wheels for collected packages: pymqi
Building wheel for pymqi (pyproject.toml) ... done
Created wheel for pymqi: filename=pymqi-1.12.11-cp39-cp39-linux_x86_64.whl size=126366 sha256=092e8d34972e8bf0bcaa138c82a50332698f2bda4db58943fb406ce86a751355
Stored in directory: /home/pesourob/.cache/pip/wheels/65/52/19/d7f548d571303b3a5c6ee2643376e9203f785d1e84202003f5
Successfully built pymqi
Installing collected packages: pymqi
Successfully installed pymqi-1.12.11
```

Tímto je instalace dokončena a můžeš začít pracovat s `pymqi` pro monitorování IBM MQ!




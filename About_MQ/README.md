# IBM MQ - Komplexní průvodce

## Obsah
1. [Úvod do IBM MQ](#úvod-do-ibm-mq)
2. [Architektura](#architektura)
3. [Instalace a Konfigurace](#instalace-a-konfigurace)
4. [MQ Objekty](#mq-objekty)
5. [Bezpečnost a Oprávnění](#bezpečnost-a-oprávnění)
6. [Monitoring a Správa](#monitoring-a-správa)
7. [Best Practices](#best-practices)
8. [Řešení Problémů](#řešení-problémů)

## Úvod do IBM MQ

### Co je IBM MQ?
IBM MQ je middleware pro asynchronní zasílání zpráv mezi aplikacemi. Poskytuje:
- Garantované doručení zpráv
- Transakční zpracování
- Vysokou dostupnost
- Škálovatelnost
- Bezpečnost

### Hlavní výhody
- Spolehlivé asynchronní zasílání zpráv
- Podpora různých platforem a programovacích jazyků
- Robustní zabezpečení
- Škálovatelnost a vysoká dostupnost
- Integrace s různými systémy

## Architektura

### Základní komponenty
1. **Queue Manager (QM)**
   - Spravuje fronty a kanály
   - Zajišťuje bezpečnost a přístupová práva
   - Řídí transakce a persistenci zpráv

2. **Queues (Fronty)**
   - Local Queues: Lokální úložiště zpráv
   - Remote Queues: Odkazy na fronty v jiných QM
   - Alias Queues: Alternativní názvy pro existující fronty
   - Model Queues: Šablony pro dynamické fronty

3. **Channels (Kanály)**
   - Sender/Receiver: Pro komunikaci mezi QM
   - Server/Requester: Pro požadavky klient-server
   - Client: Pro připojení MQ klientů
   - Cluster: Pro komunikaci v clusteru

### Komunikační modely
1. **Point-to-Point**
   ```
   Application A -> Queue -> Application B
   ```

2. **Publish/Subscribe**
   ```
   Publisher -> Topic -> Multiple Subscribers
   ```

## Instalace a Konfigurace

### Typy instalace

1. **Server Installation**
   - Plná instalace s Queue Managerem
   - Vyžaduje licence
   - Podporuje všechny funkce

2. **Client Installation**
   - Lightweight instalace pro klienty
   - Nevyžaduje licence
   - Omezená funkcionalita

### Požadované knihovny a závislosti

#### IBM MQ Client Libraries
```bash
# Základní knihovny
libmqic.so      # Core MQ client library
libmqm.so       # MQ runtime
libmqmcs.so     # Message catalog
libmqmzse.so    # Security components

# Volitelné komponenty
libmqjbind.so   # Java bindings
libmqcics.so    # CICS support
```

#### Python Dependencies
```bash
# Základní balíčky
pymqi           # IBM MQ Python interface
pyyaml          # YAML configuration support
colorama        # Terminal color support
tabulate        # Table formatting
```

### Instalační kroky

1. **Server Installation**
   ```bash
   # RPM instalace (Red Hat/CentOS)
   rpm -ivh MQSeriesRuntime-*.rpm
   rpm -ivh MQSeriesServer-*.rpm
   
   # Debian/Ubuntu
   dpkg -i ibmmq-runtime_*.deb
   dpkg -i ibmmq-server_*.deb
   ```

2. **Client Installation**
   ```bash
   # RPM instalace
   rpm -ivh MQSeriesClient-*.rpm
   
   # Debian/Ubuntu
   dpkg -i ibmmq-client_*.deb
   ```

## MQ Objekty

### Queue Manager
- Centrální komponenta pro správu MQ objektů
- Spravuje bezpečnost a přístupová práva
- Řídí transakce a persistenci zpráv

### Queues
1. **Local Queues**
   ```
   DEFINE QLOCAL('APP.QUEUE') MAXDEPTH(5000)
   ```

2. **Remote Queues**
   ```
   DEFINE QREMOTE('REMOTE.QUEUE') RNAME('LOCAL.QUEUE') RQMNAME('QM2')
   ```

3. **Alias Queues**
   ```
   DEFINE QALIAS('ALIAS.QUEUE') TARGET('ACTUAL.QUEUE')
   ```

### Channels
1. **Server-Connection**
   ```
   DEFINE CHANNEL('APP.SVRCONN') CHLTYPE(SVRCONN)
   ```

2. **Sender-Receiver Pair**
   ```
   DEFINE CHANNEL('QM1.TO.QM2') CHLTYPE(SDR) CONNAME('host(1414)') XMITQ('QM2')
   DEFINE CHANNEL('QM1.TO.QM2') CHLTYPE(RCVR)
   ```

## Bezpečnost a Oprávnění

### Autentizace

1. **Základní autentizace**
   ```bash
   # Nastavení autentizace
   ALTER AUTHINFO(SYSTEM.DEFAULT.AUTHINFO.IDPWOS) AUTHTYPE(IDPWOS) CHCKCLNT(REQUIRED)
   ```

2. **SSL/TLS Konfigurace**
   ```bash
   # Nastavení SSL na kanálu
   ALTER CHANNEL('SECURE.SVRCONN') CHLTYPE(SVRCONN) SSLCIPH(TLS_RSA_WITH_AES_128_CBC_SHA256)
   ```

### Oprávnění na objekty

1. **Queue Manager Level**
   ```bash
   # Kontrola oprávnění
   dspmqaut -m QM1 -t qmgr -p username
   
   # Nastavení oprávnění
   setmqaut -m QM1 -t qmgr -p username +connect +inq
   ```

2. **Queue Level**
   ```bash
   # Nastavení oprávnění na frontu
   setmqaut -m QM1 -t queue -n APP.QUEUE -p username +put +get +browse
   ```

### Typy oprávnění

1. **Queue Manager Permissions**
   - connect: Připojení k QM
   - inq: Dotazování na objekty
   - setid: Nastavení identity
   - altusr: Změna uživatele

2. **Queue Permissions**
   - put: Vkládání zpráv
   - get: Čtení zpráv
   - browse: Prohlížení zpráv
   - inq: Dotazování na vlastnosti

## Monitoring a Správa

### Základní monitoring

1. **Queue Manager Status**
   ```bash
   dspmq -m QM1 -x
   ```

2. **Queue Monitoring**
   ```bash
   # Kontrola hloubky front
   DISPLAY QLOCAL(*) WHERE(CURDEPTH GT 0)
   
   # Monitoring využití
   DISPLAY QSTATUS(*) TYPE(QUEUE) WHERE(IPPROCS GT 0)
   ```

3. **Channel Monitoring**
   ```bash
   # Status kanálů
   DISPLAY CHSTATUS(*) WHERE(STATUS NE INACTIVE)
   ```

### Best Practices pro Monitoring

1. **Pravidelné kontroly**
   - Queue depths
   - Channel status
   - Error logs
   - Performance metrics

2. **Alerting**
   - Nastavení thresholds pro fronty
   - Monitoring channel status
   - Sledování error logů
   - Kontrola dostupnosti služeb

## Best Practices

### Návrh a Implementace

1. **Queue Manager Design**
   - Oddělení produkčních a testovacích QM
   - Standardizované pojmenování objektů
   - Dokumentace konfigurací

2. **Security Best Practices**
   - Princip nejmenších oprávnění
   - Pravidelná revize oprávnění
   - SSL/TLS pro externí komunikaci
   - Monitoring přístupů

3. **Performance Optimization**
   - Správné nastavení MAXDEPTH
   - Monitoring využití zdrojů
   - Pravidelná údržba

### Běžné Scénáře

1. **Produkční nasazení**
   ```bash
   # 1. Vytvoření Queue Managera
   crtmqm QM1
   
   # 2. Základní konfigurace
   ALTER QMGR DEADQ('SYSTEM.DEAD.LETTER.QUEUE')
   
   # 3. Nastavení security
   ALTER AUTHINFO(SYSTEM.DEFAULT.AUTHINFO.IDPWOS) AUTHTYPE(IDPWOS) CHCKCLNT(REQUIRED)
   ```

2. **Monitoring Setup**
   ```bash
   # 1. Nastavení event monitoringu
   ALTER QMGR MONQ(MEDIUM) MONCHL(MEDIUM)
   
   # 2. Konfigurace event queues
   DEFINE QLOCAL('SYSTEM.ADMIN.QMGR.EVENT')
   ```

## Řešení Problémů

### Běžné problémy

1. **Connection Issues**
   - Kontrola status QM
   - Ověření channel status
   - Kontrola firewallu
   - Ověření oprávnění

2. **Performance Issues**
   - Monitoring queue depths
   - Kontrola channel throughput
   - Analýza error logů
   - Resource monitoring

### Diagnostické nástroje

1. **Error Logs**
   ```bash
   # Zobrazení error logů
   amqerr01.log
   ```

2. **Trace**
   ```bash
   # Zapnutí trace
   strmqtrc -m QM1
   ```

### Užitečné příkazy pro diagnostiku

```bash
# Status Queue Managera
dspmq -m QM1 -x

# Channel status
DISPLAY CHSTATUS(*)

# Queue depth
DISPLAY QLOCAL(*) WHERE(CURDEPTH GT 0)

# Active processes
DISPLAY QSTATUS(*) WHERE(IPPROCS GT 0)
``` 

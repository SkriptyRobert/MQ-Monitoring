# IBM MQ Monitorovací Řešení
## Flexibilní Monitorovací Nástroj pro IBM MQ Infrastrukturu

## 🌟 Klíčové Vlastnosti

### 💪 Výkonný Konfigurační Systém
- **Centralizovaná YAML Konfigurace**
  - Veškerá monitorovací nastavení na jednom místě
  - Čitelný formát
  - Snadná údržba a verzování

### 🎯 Přizpůsobitelné Monitorování
- **Flexibilní Výběr Objektů**
  - Monitorování specifických front pomocí vzorů
  - Filtrování systémových front
  - Monitorování kanálů pomocí zástupných znaků

### 🚨 Chytrý Systém Upozornění
- **Konfigurovatelné Úrovně Závažnosti**
  - Stavy OK, WARNING, CRITICAL, UNKNOWN
  - Vlastní prahy pro každou komponentu
  - Personalizované zprávy upozornění

### 📊 Více Formátů Výstupu
- **Vyberte si Preferovaný Formát**
  - Tabulkový pohled pro přehlednost
  - Konzolový výstup pro rychlé kontroly
  - JSON pro integraci **Možnost předání dat Logstash, Fluentd a napojení dat na Kibana, Grafana, Elasticsearch **
  - CSV pro reportování

## 🔍 Příklad Rychlého Startu

### Základní Konfigurace
```yaml
# config_v3.yaml
mq_servers:
  - name: "produkcni_mq"
    host: "mq.tamepere.fin" # nebo IP adresa
    port: 1414
    queue_managers:
      - name: "QM1"
        channel: "SYSTEM.ADMIN.SVRCONN"
        queues_to_monitor:
          - "APP.*"          # Všechny aplikační fronty
          - "SYSTEM.ADMIN.*" # Systémové admin fronty
```

### Konfigurace Vlastních Upozornění pro nastavení T3 specialistou 
```yaml
queues_monitoring:
  global:
    max_depth: 5000
    warning_depth: 1000
    messages:
      max_depth:
        severity: "CRITICAL"
        text: "Fronta {queue_name} překročila maximální hloubku {max_depth} Proveď akce Xy!"
```

## 📝 Příklady Výstupu

### Tabulkový Formát
```
+----------------+---------+------------------+
| Component      | Status  | Message         |
+----------------+---------+------------------+
| QM1            | OK      | Running         |
| APP.QUEUE.1    | WARNING | High depth (80%)|
| SYSTEM.CHANNEL | OK      | Active          |
+----------------+---------+------------------+
```

### Konzolový Výstup
```
2024-03-15 10:30:15 [OK] QM1: Queue Manager is running normally
2024-03-15 10:30:15 [WARNING] APP.QUEUE.1: Queue depth at 80% (4000/5000)
2024-03-15 10:30:15 [CRITICAL] SYSTEM.DEAD.LETTER.QUEUE: Maximum depth exceeded
```

### JSON Formát
```json
{
  "timestamp": "2024-03-15T10:30:15",
  "queue_manager": "QM1",
  "components": [
    {
      "name": "APP.QUEUE.1",
      "type": "queue",
      "status": "WARNING",
      "metrics": {
        "depth": 4000,
        "max_depth": 5000
      }
    }
  ]
}
```

## 🛠 Pokročilé Funkce pro detailní nastavení určitých front a jejich vlatností T3 specialistou v config.yaml více info v confi_template.txt

### Dynamické Prahy
```yaml
queues_monitoring:
  specific:
    APP.PRIORITY.QUEUE:
      max_depth: 1000
      warning_depth: 500
      required_consumers: 2
      messages:
        no_consumers:
          severity: "CRITICAL"
          text: "Priority queue requires minimum 2 active consumers!"
```

### Konfigurace Logování
```yaml
output:
  logging:
    enabled: true
    directory: "./logs"
    filename: "mq_monitor.log"
    max_size_mb: 10
    backup_count: 5
```

## 🔧 Technické Detaily

### Monitorovací Schopnosti

#### Monitorování Queue Manageru
- Status: RUNNING, STOPPED, ERROR
- Command levels
- Overall health check: OK, WARNING, CRITICAL

#### Monitorování Kanálů
- Status: RUNNING, STOPPED, INACTIVE
- Connection count monitoring
- Inactivity detection
- Custom thresholds

#### Monitorování Front
- Depth monitoring
- Consumer count
- Utilization percentage
- Stuck message detection
- System queue differentiation

### Bezpečnostní Funkce
- Podpora SSL/TLS
- Správa přihlašovacích údajů
- Integrace řízení přístupu

## 📈 Případy Použití

### 1. Produkční Monitoring
- Monitorování hloubky front v reálném čase
- Sledování stavu kanálů
- Sběr výkonnostních metrik

### 2. Systémová Administrace
- Kontroly zdraví Queue Manageru
- Monitorování systémových front
- Sledování využití zdrojů

### 3. Podpora Aplikací
- Monitorování aplikačních front
- Kontroly dostupnosti konzumentů
- Sledování toku zpráv

## 🚀 Začínáme

1. Instalace Požadavků:
```bash
pip install pymqi pyyaml colorama tabulate
```

2. Konfigurace Prostředí:
```bash
# Nastavení proměnných prostředí (volitelné)
export MQ_MONITORING_CONFIG=/cesta/k/config_v3.yaml
```

3. Spuštění Monitoru:
```bash
python mq_monitor_v3.py -c config_v3.yaml
```

## 📚 Dokumentace

Kompletní dokumentaci naleznete v [mq_monitor_v3.txt](mq_monitor_v3.txt)

## 🤝 Podpora

Pro technickou podporu a požadavky na nové funkce kontaktujte:
- Email: robert.pesout@tietoevry.com

## 📋 Historie Verzí

### v3.0.0 (Aktuální)
- Více formátů výstupu
- Vylepšená podpora SSL/TLS
- Vylepšené zpracování chyb
- Vlastní konfigurace front
- Pokročilý systém logování

## 🔒 Bezpečnostní Doporučení

1. Používejte proměnné prostředí pro citlivá data
2. Povolte SSL/TLS pro všechna připojení
3. Implementujte správné řízení přístupu
4. Pravidelné bezpečnostní audity

## 💡 Osvědčené Postupy

1. Začněte s minimálním monitorováním
2. Postupně přidávejte komponenty
3. Nastavte vhodné prahy
4. Pravidelná revize konfigurace
5. Sledujte velikosti log souborů

## 🛑 Řešení Problémů

Běžné problémy a řešení:
1. Problémy s připojením
2. Problémy s výkonem
3. Chyby konfigurace

Podrobný průvodce řešením problémů naleznete v [mq_monitor_v3.txt](mq_monitor_v3.txt) 

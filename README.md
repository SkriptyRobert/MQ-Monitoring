🔹 IBM MQ – klíčové pojmy a architektura
🔹 Queue Manager (QM) – hlavní součást IBM MQ, spravuje a zpracovává zprávy v různých frontách.
🔹 Queue (Fronta) – místo, kam aplikace posílají a odkud přijímají zprávy.
🔹 Channel (Kanál) – komunikační cesta mezi dvěma systémy nebo queue managery.
🔹 Message (Zpráva) – data přenášená mezi aplikacemi pomocí IBM MQ.
🔹 Listener (Posluchač) – proces, který čeká na spojení a přijímá zprávy.

Jak to funguje?
1️⃣ Aplikace 1 pošle zprávu do fronty (PUT).
2️⃣ IBM MQ zprávu uchová v queue manageru.
3️⃣ Aplikace 2 si zprávu vyzvedne (GET).
4️⃣ Pokud příjemce neexistuje, zpráva může čekat až do jeho spuštění.

📌 Výhoda IBM MQ: Pokud příjemce neběží, zpráva se neztratí (pokud je persistentní).

🔹 Jak se naše DEMO liší od produkce?
Funkce	Naše DEMO (Docker)	Produkční IBM MQ
Queue Manager	QM1 (jeden)	Více QM pro HA
Uživatelé & Role	admin/passw0rd	LDAP, Kerberos, RBAC
Zabezpečení (TLS)	❌ Neaktivní	✅ Povinné šifrování
Trvalé zprávy	❌ Volitelné	✅ Nutné pro HA
Monitoring	❌ Ruční dotazy	✅ IBM Monitoring
👉 Chceš přidat bezpečnost a autentizaci do testovacího prostředí? To bychom museli přidat TLS a správu uživatelů.

🔹 Co je součástí našeho testovacího prostředí?
✔ Queue Manager: QM1 (spravuje fronty)
✔ Dvě testovací fronty: DEV.QUEUE.1, DEV.QUEUE.2
✔ Možnost posílat zprávy pomocí Pythonu
✔ CLI příkazy pro kontrolu front
✔ Automatické posílání zpráv (simulace trafficu)

Co chybí oproti produkci?
❌ TLS zabezpečení (můžeme přidat, pokud chceš)
❌ Víc queue managerů pro HA
❌ Alerty a logování

Chceš to rozšířit o bezpečnost a monitoring? Dej vědět! 🚀

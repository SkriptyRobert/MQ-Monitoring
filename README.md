# MQ-Monitoring
Home lab - IBM MQ configured in container with all function. Target is a create python monitoring. 

## Technology termins 

🔹 IBM MQ – klíčové pojmy a architektura

🔹 Queue Manager (QM) – hlavní součást IBM MQ, spravuje a zpracovává zprávy v různých frontách.
🔹 Queue (Fronta) – místo, kam aplikace posílají a odkud přijímají zprávy.
🔹 Channel (Kanál) – komunikační cesta mezi dvěma systémy nebo queue managery.
🔹 Message (Zpráva) – data přenášená mezi aplikacemi pomocí IBM MQ.
🔹 Listener (Posluchač) – proces, který čeká na spojení a přijímá zprávy.

## How all works

1️⃣ Aplikace 1 pošle zprávu do fronty (PUT).
2️⃣ IBM MQ zprávu uchová v queue manageru.
3️⃣ Aplikace 2 si zprávu vyzvedne (GET).
4️⃣ Pokud příjemce neexistuje, zpráva může čekat až do jeho spuštění.

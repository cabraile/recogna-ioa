About
---
Repositório de estudos sobre IoA internos


Demos
---
* Servidor (lampada e sensor de umidade): `uv run python apps/demo_wot_client.py`
  * `http://localhost:8888/`: Lista de TD
  * `http://localhost:8888/0`: TD da lâmpada
  * `http://localhost:8888/1`: TD do sensor de umidade
* Cliente: `uv run python apps/demo_wot_dummy_client.py $thing`
  * Opcional: argumento `$thing` para escolher se vai manipular a lâmpada (`lamp`, padrão) ou se vai monitorar o sensor de umidade (`sensor`).
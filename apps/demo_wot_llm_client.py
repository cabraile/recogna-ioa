"""Nesta demo um LLM vai receber os TD da rede, vai receber um prompt, e vai tomar as decisões baseadas neste."""

import time
import asyncio
from langchain_community.llms import CTransformers

from recogna_ioa.web_thing_client import WebThingClient
from recogna_ioa.agents import (
    ThingSelectorAgent,
    ThingActionSelectorAgent,
    ThingActionSelectionAgentReturnCode,
)


async def main():
    prompt = "Está muito escuro, gostaria que ficasse mais claro."

    # Iniciar os agentes
    llm = CTransformers(
        model="recogna-nlp/bode-7b-alpaca-pt-br-gguf",
        model_file="bode-7b-alpaca-q8_0.gguf",
        model_type="llama",
        config={
            "temperature": 0.0,
            "max_new_tokens": 256,
            "repetition_penalty": 1.2,
        },
    )
    thing_selector_agent = ThingSelectorAgent(llm_model=llm)
    thing_action_selector_agent = ThingActionSelectorAgent(llm_model=llm)

    # Iniciar a comunicação com o servidor de WoT
    client = WebThingClient("http://localhost:8888")
    thing_description_list = client.available_things

    # Passo 1: Obter a Thing relevante para o prompt
    print("SELEÇÃO DO THING")
    print("=" * 8)
    time_start = time.time()
    selected_thing_id: str = thing_selector_agent.run(
        input_text=prompt,
        thing_description_list=thing_description_list,
    )
    duration_sec = time.time() - time_start
    print(
        f"> O agente decidiu usar o Thing {selected_thing_id} (raciocinou por {duration_sec:.2f}s)"
    )

    # Passo 2: Verificar dentro das ações possíveis para a Thing qual é a mais indicada e seus parâmetros
    print("=" * 8)
    print("SELEÇÃO DA AÇÃO")
    print("=" * 8)
    selected_thing_idx = client.lookup_thing_idx_by_id(selected_thing_id)
    target_thing_description = thing_description_list[selected_thing_idx]
    target_thing_state = await client.get_properties(index=selected_thing_idx)
    time_start = time.time()
    action_outcome = thing_action_selector_agent.run(
        prompt,
        target_thing_description,
        thing_state=target_thing_state,
    )
    duration_sec = time.time() - time_start
    print(f"> O agente raciocinou sobre a ação por {duration_sec:.2f}s")
    print("> Código de retorno: ", action_outcome.code.name)
    print("> Saída obtida sem processamento")
    print("```")
    print(action_outcome.output)
    print("```")

    # Passo 3: Executar
    if action_outcome.code == ThingActionSelectionAgentReturnCode.SUCCESS:
        out_dict = action_outcome.parsed_output
        action_id = list(out_dict.keys())[0]
        params_dict = out_dict[action_id]["input"]
        print(f"Executando a ação '{action_id}' com parâmetros", end="")
        for param_name, param_value in params_dict.items():
            print(f" '{param_name}':'{param_value}'", end="")
        print()
        res = await client.run_action(action_name=action_id, input_data=params_dict)
        if res:
            print("A ação foi executada com sucesso. Resultado: ")
            print(res)
        else:
            print("Falha em executar a ação")


if __name__ == "__main__":
    asyncio.run(main())

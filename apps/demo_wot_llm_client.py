"""Nesta demo um LLM vai receber os TD da rede, vai receber um prompt, e vai tomar as decisões baseadas neste."""

import asyncio
from langchain.prompts import PromptTemplate
from langchain_community.llms import CTransformers

from recogna_ioa.web_thing_client import WebThingClient


LLM_MODEL = CTransformers(
    model="recogna-nlp/bode-7b-alpaca-pt-br-gguf",
    model_file="bode-7b-alpaca-q8_0.gguf",
    model_type="llama",
    config={
        "temperature": 0.0,
        "max_new_tokens": 128,
    },
)

TOOL_SELECTOR_AGENT_PROMPT_TEMPLATE = """### Instruções
Você é um agente controlador de dispositivos em uma rede doméstica.
Você deve escolher dentre as opções de dispositivos abaixo o mais apropriado para a pergunta do usuário.

```
{available_thing_ids_and_descriptions_str}
```

Note que o que antecede o `:` corresponde ao ID e o resto corresponde à descrição.
Sua resposta deve ser exatamente uma string contendo o ID do dispositivo mais relevante para o pedido do usuário.

### Entrada

{input_text}

### Resultado
"""


class ToolSelectorAgent:

    def __init__(self):
        self.prompt = PromptTemplate(
            template=TOOL_SELECTOR_AGENT_PROMPT_TEMPLATE,
            input_variables=["available_thing_ids_and_descriptions_str", "input_text"],
        )
        self.llm_chain = self.prompt | LLM_MODEL

    def run(self, input_text: str, thing_description_list: list[dict]) -> str:
        """Returns the relevant device ID"""
        thing_description_str = make_id_description_pair_lines(thing_description_list)
        inputs = {
            "input_text": input_text,
            "available_thing_ids_and_descriptions_str": thing_description_str,
        }
        response = self.llm_chain.invoke(inputs)

        # Debug purposes only
        full_prompt = self.prompt.format(**inputs)
        print("Prompt: ```")
        print(full_prompt)
        print("```")

        return response


def make_id_description_pair_lines(thing_description_list: list[dict[str, any]]) -> str:
    pair_strs = [
        f"{thing['id']}: {thing['description']}" for thing in thing_description_list
    ]
    return "\n".join(pair_strs)


async def main():
    client = WebThingClient("http://localhost:8888")
    agent = ToolSelectorAgent()
    print(
        agent.run(
            "Está muito escuro, gostaria que ficasse mais claro.",
            client.available_things,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

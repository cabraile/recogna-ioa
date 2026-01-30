from enum import Enum
import json
import re
from typing import Any
from pydantic import BaseModel, ConfigDict
from langchain.prompts import PromptTemplate
from langchain_community.llms import CTransformers


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


def make_id_description_pair_lines(thing_description_list: list[dict[str, any]]) -> str:
    pair_str_list = [
        f"{thing['id']}: {thing['description']}" for thing in thing_description_list
    ]
    return "\n".join(pair_str_list)


class ThingSelectorAgent:
    """This agent selects the best thing to address the user's prompt."""

    def __init__(self, llm_model: CTransformers):
        self.prompt = PromptTemplate(
            template=TOOL_SELECTOR_AGENT_PROMPT_TEMPLATE,
            input_variables=["available_thing_ids_and_descriptions_str", "input_text"],
        )
        self.llm_chain = self.prompt | llm_model

    def run(self, input_text: str, thing_description_list: list[dict[str, any]]) -> str:
        """Returns the relevant device ID"""
        thing_description_str = make_id_description_pair_lines(thing_description_list)
        inputs = {
            "input_text": input_text,
            "available_thing_ids_and_descriptions_str": thing_description_str,
        }
        response = self.llm_chain.invoke(inputs).strip()

        # Debug purposes only
        full_prompt = self.prompt.format(**inputs)
        print("Prompt: ```")
        print(full_prompt)
        print("```")
        print("Response: ", response)

        # TODO: verificar se ferramenta existe ou se não é para selecionar nenhuma ferramenta.

        return response


THING_ACTION_SELECTOR_AGENT_PROMPT_TEMPLATE = """### Instrução
Você é um sistema de automação residencial. Sua tarefa é converter um pedido do usuário em uma chamada de ação JSON para o dispositivo descrito abaixo.

REGRAS:
1. Responda APENAS com o JSON.
2. Use o formato: {{$NOME_DA_AÇÃO: {{"input": {{...}} }} }}
3. Troque o "$NOME_DA_AÇÃO" pelo id da ação na chave JSON
4. Ajuste os valores dos parâmetros de acordo com o desejo do usuário.
5. Caso não haja ação relevante com o prompt de entrada, retorne um json vazio.


DISPOSITIVO ATUAL:
{thing_description}

ESTADO ATUAL:
{thing_state}

AÇÕES DISPONÍVEIS:
{available_thing_ids_and_descriptions_str}

### Entrada:
Usuário: "{input_text}"

### Resposta:
{{"""


def make_action_description_pair_lines(thing_description: dict[str, any]) -> str:
    return json.dumps(thing_description["actions"])


class ThingActionSelectionAgentReturnCode(Enum):
    SUCCESS = 0
    FAILED_JSON_STRUCTURE = 1
    FAILED_ACTION_DOES_NOT_EXIST = 2
    FAILED_NO_ACTION_MATCHES_THE_USER_NEEDS = 3


class ThingActionSelectionAgentOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    code: ThingActionSelectionAgentReturnCode
    prompt: str = ""
    output: str = ""
    parsed_output: dict[str, Any] = {}


class ThingActionSelectorAgent:
    """This agent selects the best action given the prompt and selected thing."""

    def __init__(self, llm_model: CTransformers):
        self.prompt = PromptTemplate(
            template=THING_ACTION_SELECTOR_AGENT_PROMPT_TEMPLATE,
            input_variables=[
                "thing_description",
                "available_thing_ids_and_descriptions_str",
                "input_text",
            ],
        )
        self.llm_chain = self.prompt | llm_model

    def run(
        self,
        input_text: str,
        thing_description: dict[str, any],
        thing_state: dict[str, any],
    ) -> ThingActionSelectionAgentOutput:
        """Returns the relevant action ID"""
        thing_description_str = make_action_description_pair_lines(thing_description)
        thing_state_str = json.dumps(thing_state)
        inputs = {
            "thing_description": thing_description["description"],
            "input_text": input_text,
            "available_thing_ids_and_descriptions_str": thing_description_str,
            "thing_state": thing_state_str,
        }
        response = "{" + self.llm_chain.invoke(inputs).strip()
        json_match = re.search(r"\{.*?\}", response, re.DOTALL)

        prompt_output = self.prompt.format(**inputs)
        output_json = {}
        if not json_match:
            return ThingActionSelectionAgentOutput(
                code=ThingActionSelectionAgentReturnCode.FAILED_JSON_STRUCTURE,
                prompt=prompt_output,
                output=response,
            )
        if "\{\}" in response:
            return ThingActionSelectionAgentOutput(
                code=ThingActionSelectionAgentReturnCode.FAILED_NO_ACTION_MATCHES_THE_USER_NEEDS,
                prompt=prompt_output,
                output=response,
            )
        try:
            output_json = json.loads(json_match.group(0).replace("\n", "").strip())
        except Exception:
            return ThingActionSelectionAgentOutput(
                code=ThingActionSelectionAgentReturnCode.FAILED_JSON_STRUCTURE,
                prompt=prompt_output,
                output=response,
            )
        if list(output_json.keys())[0] not in thing_description["actions"]:
            return ThingActionSelectionAgentOutput(
                code=ThingActionSelectionAgentReturnCode.FAILED_ACTION_DOES_NOT_EXIST,
                prompt=prompt_output,
                output=response,
            )

        return ThingActionSelectionAgentOutput(
            code=ThingActionSelectionAgentReturnCode.SUCCESS,
            prompt=prompt_output,
            output=response,
            parsed_output=output_json,
        )

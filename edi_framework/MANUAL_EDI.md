# Manual do EDI Framework

## Objetivo

Este manual explica:

- o que precisa ser cadastrado
- a ordem recomendada dos cadastros
- como iniciar um processo EDI
- como usar documentos do Odoo como origem
- como usar payload externo como origem
- exemplos práticos com fatura do Odoo (`account.move`)

O desenho atual do framework suporta dois modos principais:

- `process_code + record`
- `process_code + payload`

O chamador ideal não precisa conhecer `backend`, `layout` e `exchange_type`. Ele informa qual processo EDI quer executar e qual é a origem.

## Conceitos principais

### 1. `edi.process`

É o cadastro principal para uso funcional.

Um `edi.process` define:

- qual `backend` usar
- qual `exchange_type` usar
- qual `layout` usar
- qual direção usar
- se deve enfileirar automaticamente
- opcionalmente qual modelo do Odoo pode usar esse processo

Na prática, este é o identificador que o sistema chamador deve usar:

```python
process_code="nfe_saida"
```

### 2. `edi.transaction`

É o cabeçalho da operação EDI.

Representa o processo de negócio e concentra:

- vínculo com o documento de origem
- estado técnico
- estado de negócio
- exchange atual
- logs
- eventos

É o registro que normalmente deve ser gravado no documento de origem.

Exemplo:

- a fatura grava `edi_transaction_id`

### 3. `edi.exchange`

É a execução concreta.

Uma transação pode ter uma ou mais exchanges. A exchange guarda:

- payloads
- snapshots de origem
- dados de API
- dados de arquivo
- job de fila

### 4. `edi.layout`

Define a estrutura do dado que será montado ou lido.

O layout contém:

- fontes (`edi.layout.source`)
- registros (`edi.layout.record`)
- campos (`edi.layout.field`)

### 5. `edi.extract.map`

Define como os dados de origem são extraídos e transformados para produzir o payload normalizado.

### 6. `edi.data.source`

Define de onde vêm os dados.

Tipos já previstos no framework:

- `odoo_model`
- `sql_view`
- `sql_query`
- `sql_procedure`
- `api`
- `python`
- `csv`
- `json`
- `xml`
- `array`

### 7. `edi.data.target`

Define para onde os dados serão enviados.

Tipos já previstos:

- `odoo_model`
- `sql_table`
- `sql_procedure`
- `api`
- `python`
- `file`
- `staging`

### 8. `edi.return.map`

Define como o resultado final é aplicado no destino.

## Ordem recomendada de cadastro

A ordem abaixo evita retrabalho:

### Ordem macro

1. Cadastrar `Exchange Type`
2. Cadastrar `Exchange State`
3. Cadastrar `Backend`
4. Cadastrar `Layout`
5. Cadastrar `Data Source`
6. Vincular fontes ao layout
7. Cadastrar registros e campos do layout
8. Cadastrar regras de transformação
9. Cadastrar `Extract Map`
10. Cadastrar `Data Target`
11. Cadastrar `Return Map`
12. Cadastrar `Processo EDI`

### Ordem detalhada

#### 1. Tipo de exchange

Menu:

- `EDI Framework > Configurações > Backends`

Modelo:

- `edi.exchange.type`

Defina:

- `name`
- `code`
- `category`
- `direction`

Exemplos:

- `nfe_transmissao`
- `nfse_envio`
- `cnab_remessa`
- `cnab_retorno`
- `invoice_json_export`
- `invoice_xml_export`

Observação:

- `category` é classificação técnica
- o código do processo de negócio deve ficar em `code`

#### 2. Estados do exchange

Modelo:

- `edi.exchange.state`

Cadastre pelo menos:

- `draft`
- `success`
- `error`

Opcionalmente:

- `processing`
- `waiting`
- `cancelled`

#### 3. Backend

Modelo:

- `edi.backend`

Defina:

- empresa
- tipo de backend
- configuração técnica
- canal de fila
- layout padrão opcional
- exchange type padrão opcional

Exemplos:

- SEFAZ
- prefeitura
- banco
- SFTP
- API de parceiro

#### 4. Layout

Modelo:

- `edi.layout`

Defina:

- `code`
- `format_type`
- `direction`
- backend relacionado

Exemplos:

- `NFE_4_00_JSON`
- `NFE_4_00_XML`
- `CNAB240_REMESSA`
- `CNAB240_RETORNO`

#### 5. Fonte de dados

Modelo:

- `edi.data.source`

Defina como o dado será carregado.

Exemplos:

- buscar linhas da fatura por Python
- consumir um JSON externo
- ler CSV externo
- ler XML externo
- usar array já recebido

#### 6. Vincular fonte ao layout

Modelo:

- `edi.layout.source`

Aqui você liga a fonte ao layout e define o alias.

Exemplo:

- alias `invoice`
- alias `items`
- alias `docs`

#### 7. Registros e campos do layout

Modelos:

- `edi.layout.record`
- `edi.layout.field`

Aqui você define a estrutura lógica de saída/entrada.

Exemplo para fatura:

- registro `header`
- registro `detail`
- campo `invoice_number`
- campo `customer_document`
- campo `amount_total`
- campo `due_date`

#### 8. Regras de transformação

Modelo:

- `edi.transform.rule`

Exemplos:

- `zfill`
- `multiply`
- `date_format`
- `value_map`
- `substring`

#### 9. Mapa de extração

Modelo:

- `edi.extract.map`

Defina:

- de qual alias/fonte vem o dado
- qual caminho da origem será usado
- qual campo do layout receberá o valor
- quais transformações aplicar

#### 10. Destino

Modelo:

- `edi.data.target`

Defina:

- API
- arquivo
- staging
- python
- modelo Odoo

#### 11. Mapa de retorno

Modelo:

- `edi.return.map`

Defina como o payload normalizado será entregue ao destino.

#### 12. Processo EDI

Modelo:

- `edi.process`

Este é o cadastro final que será usado pela chamada.

Defina:

- `code`
- `backend_id`
- `exchange_type_id`
- `layout_id`
- `direction`
- `auto_enqueue`
- `model_name` se quiser restringir a um modelo específico

Exemplo:

- `nfe_saida`
- `invoice_json_export`
- `invoice_xml_export`
- `cnab_retorno_import`

## Resumo do que o sistema chamador precisa saber

Depois dos cadastros acima, o sistema chamador precisa saber apenas:

- qual `process_code` quer executar
- qual é a origem

A origem pode ser:

- um registro do Odoo
- um payload externo

## Como chamar

## 1. Chamada com documento do Odoo

Use quando a origem for um registro interno.

Exemplo:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="nfe_saida",
    record=invoice,
)
```

Equivalente explícito:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="nfe_saida",
    res_model="account.move",
    res_id=invoice.id,
)
```

O retorno é um registro `edi.transaction`.

Você normalmente grava isso na origem:

```python
invoice.edi_transaction_id = transaction.id
```

## 2. Chamada com payload JSON

Use quando a origem vier pronta de fora do Odoo.

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="json_entrada",
    payload=[{"document_number": "EXT-1"}],
    payload_format="json",
    payload_name="entrada.json",
    payload_metadata={"source": "api"},
)
```

## 3. Chamada com payload CSV

```python
csv_text = \"\"\"invoice_number,amount_total
FAT-001,150.00
FAT-002,210.50
\"\"\"

transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="cnab_retorno_import",
    payload=csv_text,
    payload_format="csv",
    payload_name="retorno.csv",
)
```

## 4. Chamada com payload XML

```python
xml_text = \"\"\"<rows>
  <row>
    <invoice_number>FAT-001</invoice_number>
    <amount_total>150.00</amount_total>
  </row>
</rows>\"\"\"

transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_xml_import",
    payload=xml_text,
    payload_format="xml",
    payload_name="entrada.xml",
)
```

## 5. Chamada com payload array

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_array_import",
    payload=[
        {"invoice_number": "FAT-001", "amount_total": 150.0},
        {"invoice_number": "FAT-002", "amount_total": 210.5},
    ],
    payload_format="array",
)
```

## Uso com mixin genérico

Se o modelo de origem herdar `edi.transaction.mixin`, ele ganha:

- `edi_transaction_id`
- `action_start_edi_transaction()`
- `action_open_edi_transaction()`

Exemplo:

```python
from odoo import models


class AccountMove(models.Model):
    _inherit = ["account.move", "edi.transaction.mixin"]

    def action_send_nfe(self):
        self.ensure_one()
        transaction = self.action_start_edi_transaction(
            process_code="nfe_saida"
        )
        return transaction
```

## Exemplo completo com fatura do Odoo

Observação:

- `account.move` existe no Odoo quando o módulo `account` está instalado
- o exemplo abaixo assume que a fatura é `account.move`

### Cenário A: enviar fatura para JSON

Objetivo:

- usar `account.move` como origem
- gerar payload JSON
- enviar para API ou arquivo

Cadastros:

1. `edi.exchange.type`

- `code = invoice_json_export`
- `category = api` ou `file_generate`
- `direction = out`

2. `edi.backend`

- backend do parceiro ou integração

3. `edi.layout`

- `code = INVOICE_JSON`
- `format_type = json`
- `direction = out`

4. `edi.data.source`

- tipo `python` ou `odoo_model`
- deve montar dataset a partir de `res_model = account.move` e `res_id = invoice.id`

Exemplo de ideia da fonte Python:

```python
invoice = env[context["res_model"]].browse(context["res_id"])
result = [{
    "invoice_number": invoice.name,
    "partner_name": invoice.partner_id.name,
    "amount_total": invoice.amount_total,
}]
```

5. `edi.layout.source`

- alias `invoice`

6. `edi.layout.record` / `edi.layout.field`

- `invoice_number`
- `partner_name`
- `amount_total`

7. `edi.extract.map`

- mapeia os dados da fatura para o layout

8. `edi.data.target`

- API ou file

9. `edi.return.map`

- entrega o payload ao destino

10. `edi.process`

- `code = invoice_json_export`
- aponta para backend, exchange type e layout
- `model_name = account.move`

Chamada:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_json_export",
    record=invoice,
)
```

### Cenário B: enviar fatura para XML

Mesmo desenho do JSON, mudando:

- `edi.exchange.type.code = invoice_xml_export`
- `edi.layout.code = INVOICE_XML`
- `edi.layout.format_type = xml`

Chamada:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_xml_export",
    record=invoice,
)
```

### Cenário C: gerar remessa CNAB a partir da fatura

Objetivo:

- usar dados da fatura
- transformar para layout CNAB
- enviar para arquivo

Cadastros:

- `edi.exchange.type.code = cnab_remessa`
- `edi.layout.code = CNAB240_REMESSA`
- `edi.layout.format_type = fixed` ou `delimited`, conforme sua implementação
- `edi.data.target.type = file`
- `edi.process.code = invoice_cnab_remessa`

Chamada:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_cnab_remessa",
    record=invoice,
)
```

### Cenário D: importar retorno externo CSV/XML/JSON

Aqui a origem não é a fatura do Odoo, e sim um payload externo.

Exemplo CSV:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="cnab_retorno_import",
    payload=csv_text,
    payload_format="csv",
    payload_name="retorno.csv",
)
```

Exemplo JSON:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_json_import",
    payload=response_json,
    payload_format="json",
)
```

Exemplo XML:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_xml_import",
    payload=xml_text,
    payload_format="xml",
)
```

## Como a fonte recebe o contexto

Durante o processamento, as fontes recebem um contexto com:

- `exchange_id`
- `res_model`
- `res_id`
- `input_payload`
- `input_payload_format`
- `input_filename`
- `input_metadata`

Ou seja:

- se a origem for registro do Odoo, use `res_model` e `res_id`
- se a origem for payload externo, use `input_payload`

## Estratégia recomendada

### Para documentos internos do Odoo

Padrão recomendado:

- usar `process_code + record`

Exemplo:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="nfe_saida",
    record=invoice,
)
```

### Para integrações externas

Padrão recomendado:

- usar `process_code + payload`

Exemplo:

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_xml_import",
    payload=xml_text,
    payload_format="xml",
)
```

## O que gravar no documento de origem

O ideal é gravar:

- `edi_transaction_id`

Não é recomendável gravar só um número textual solto se você pode manter relacionamento com `edi.transaction`.

Vantagens:

- auditoria completa
- navegação até logs e eventos
- acesso ao exchange atual
- histórico de reprocessamentos

## Boas práticas

### 1. Sempre usar `edi.process`

Não exponha `backend`, `layout` e `exchange_type` ao código chamador se não houver necessidade.

### 2. Use `model_name` no processo quando fizer sentido

Isso evita chamar um processo de nota fiscal em um modelo incorreto.

### 3. Separe processos por intenção de negócio

Exemplos bons:

- `nfe_saida`
- `nfse_envio`
- `invoice_json_export`
- `invoice_xml_export`
- `cnab_retorno_import`

Exemplos ruins:

- `api1`
- `layout_a`
- `proc_teste`

### 4. Trate importação e exportação como processos diferentes

Mesmo quando falam da mesma entidade de negócio, normalmente devem ser processos distintos.

### 5. Grave sempre a transação na origem

Se a origem for um documento do Odoo, mantenha `Many2one` para `edi.transaction`.

## Checklist mínimo de implantação

Antes de chamar um processo pela primeira vez, confirme:

1. Existe `edi.process`
2. O processo aponta para backend, exchange type e layout
3. O layout tem fonte vinculada
4. O layout tem registros e campos
5. Existe `extract.map`
6. Se houver envio, existe target e return map
7. O `process_code` está correto
8. O documento de origem ou payload está sendo passado corretamente

## Cadastro mínimo para subir o primeiro processo

Se o objetivo for colocar o primeiro processo EDI no ar com o menor caminho possível, faça nesta ordem:

1. Crie um `edi.exchange.type`
2. Crie ao menos os estados `draft`, `success` e `error`
3. Crie um `edi.backend`
4. Crie um `edi.layout`
5. Crie uma `edi.data.source`
6. Vincule a fonte ao layout em `edi.layout.source`
7. Crie ao menos um `edi.layout.record`
8. Crie os `edi.layout.field` que vão compor o payload normalizado
9. Crie os `edi.extract.map`
10. Se houver envio externo, crie `edi.data.target`
11. Se houver envio externo, crie `edi.return.map`
12. Crie o `edi.process`

### Menor cenário funcional de saída

Para gerar uma primeira saída funcional, o mínimo é:

- `exchange_type`
- `exchange_state`
- `backend`
- `layout`
- `data_source`
- `layout_source`
- `layout_record`
- `layout_field`
- `extract_map`
- `process`

Se você quiser apenas testar normalização interna, isso já basta.

### Menor cenário funcional com envio

Se você quiser também enviar o resultado para algum destino:

- tudo do cenário mínimo de saída
- `data_target`
- `return_map`

## Exemplo real baseado no demo do módulo

O módulo já traz um exemplo real em [edi_demo_data.xml](/proj_edi_odoo/edi_framework/data/edi_demo_data.xml).

Esse demo mostra um fluxo completo:

- tipo de exchange `demo_api_out`
- estados `draft`, `success`, `error`
- backend `DEMO_API`
- layout `DEMO_NFSE`
- fonte `DEMO_SOURCE_DOCS`
- record `DET`
- campos `document_number`, `amount`, `customer_name`
- extract maps correspondentes
- target `DEMO_TARGET_API`
- return map `DEMO_TARGET_API`

O demo é útil porque mostra uma sequência coerente de cadastro e pode servir como referência para um primeiro processo real.

### Leitura do demo em ordem lógica

1. `edi.exchange.type`

- `demo_api_out`

2. `edi.exchange.state`

- `draft`
- `success`
- `error`

3. `edi.backend`

- `DEMO_API`

4. `edi.layout`

- `DEMO_NFSE`

5. `edi.data.source`

- `DEMO_SOURCE_DOCS`

6. `edi.layout.source`

- alias `docs`

7. `edi.layout.record`

- `DET`

8. `edi.layout.field`

- `document_number`
- `amount`
- `customer_name`

9. `edi.extract.map`

- mapas para os três campos

10. `edi.map.rule.line`

- `zfill`
- `multiply`

11. `edi.data.target`

- `DEMO_TARGET_API`

12. `edi.return.map`

- chamada do provider API

Esse fluxo hoje já está instalado no módulo e ajuda a validar o entendimento dos cadastros.

## Exemplos finais de chamada

### Documento interno

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_json_export",
    record=invoice,
)
```

### Documento interno com mixin

```python
transaction = invoice.action_start_edi_transaction(
    process_code="invoice_json_export"
)
```

### Payload externo JSON

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_json_import",
    payload=[{"invoice_number": "FAT-001"}],
    payload_format="json",
)
```

### Payload externo CSV

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_csv_import",
    payload=csv_text,
    payload_format="csv",
    payload_name="entrada.csv",
)
```

### Payload externo XML

```python
transaction = self.env["edi.transaction.service"].start_transaction(
    process_code="invoice_xml_import",
    payload=xml_text,
    payload_format="xml",
    payload_name="entrada.xml",
)
```

## Exemplo concreto em `account.move`

Este exemplo mostra como acoplar o framework a faturas do Odoo quando o módulo `account` estiver instalado.

### Objetivo

- adicionar `edi_transaction_id` na fatura
- adicionar um botão para disparar o processo EDI
- chamar apenas `process_code`

### Modelo Python

```python
from odoo import models


class AccountMove(models.Model):
    _inherit = ["account.move", "edi.transaction.mixin"]

    def _edi_transaction_start_values(self):
        self.ensure_one()
        values = super()._edi_transaction_start_values()
        values.update(
            {
                "process_code": "invoice_json_export",
            }
        )
        return values

    def action_send_invoice_edi(self):
        self.ensure_one()
        transaction = self.action_start_edi_transaction()
        return self.action_open_edi_transaction()
```

### Variante com múltiplos formatos

Se a mesma fatura puder ser enviada em vários formatos, use métodos separados:

```python
from odoo import models


class AccountMove(models.Model):
    _inherit = ["account.move", "edi.transaction.mixin"]

    def action_send_invoice_json(self):
        self.ensure_one()
        return self.action_start_edi_transaction(
            process_code="invoice_json_export"
        )

    def action_send_invoice_xml(self):
        self.ensure_one()
        return self.action_start_edi_transaction(
            process_code="invoice_xml_export"
        )

    def action_send_invoice_cnab(self):
        self.ensure_one()
        return self.action_start_edi_transaction(
            process_code="invoice_cnab_remessa"
        )
```

### View da fatura com campo e botão

Exemplo de herança XML:

```xml
<odoo>
    <record id="view_move_form_inherit_edi" model="ir.ui.view">
        <field name="name">account.move.form.edi</field>
        <field name="model">account.move</field>
        <field name="inherit_id" ref="account.view_move_form"/>
        <field name="arch" type="xml">
            <xpath expr="//sheet" position="inside">
                <group string="EDI">
                    <field name="edi_transaction_id"/>
                </group>
            </xpath>
            <xpath expr="//header" position="inside">
                <button
                    name="action_send_invoice_json"
                    type="object"
                    string="Enviar JSON"
                    class="btn-primary"
                />
                <button
                    name="action_send_invoice_xml"
                    type="object"
                    string="Enviar XML"
                />
                <button
                    name="action_send_invoice_cnab"
                    type="object"
                    string="Gerar CNAB"
                />
            </xpath>
        </field>
    </record>
</odoo>
```

### Como isso fica para o usuário

O fluxo de uso fica:

1. usuário abre a fatura
2. clica no botão do formato desejado
3. o sistema chama `process_code`
4. cria a `edi.transaction`
5. grava `edi_transaction_id` na fatura
6. cria a `edi.exchange`
7. enfileira ou processa
8. o usuário pode abrir a transação e auditar tudo

## Processo sugerido para fatura em vários formatos

Uma modelagem simples e clara é ter um processo por intenção:

- `invoice_json_export`
- `invoice_xml_export`
- `invoice_cnab_remessa`
- `invoice_json_import`
- `invoice_xml_import`

Isso é melhor do que tentar usar um único processo com comportamento variável, porque:

- simplifica a chamada
- simplifica a auditoria
- evita lógica condicional no chamador
- facilita separar layouts e destinos

## Recomendações finais de implantação

### Para o primeiro uso

Comece com um processo simples:

- uma fonte `python`
- um layout JSON pequeno
- um target `api` ou `file`
- um `process_code` claro

Exemplo:

- `invoice_json_export`

### Para evolução posterior

Depois evolua para:

- XML fiscal
- CNAB
- importação CSV/XML/JSON
- múltiplos destinos
- múltiplos processos por documento

### Regra de desenho recomendada

Pense sempre assim:

- o documento de origem não conhece detalhes técnicos
- o documento só conhece o `process_code`
- o framework resolve o resto via cadastro

## Arquitetura resumida

- `edi.process`: o que o chamador seleciona
- `edi.transaction`: o que o chamador grava na origem
- `edi.exchange`: a execução concreta
- `edi.layout`: a estrutura
- `edi.data.source`: de onde vem o dado
- `edi.extract.map`: como o dado é transformado
- `edi.data.target`: para onde vai
- `edi.return.map`: como aplica o resultado

## Conclusão

Para uso normal do framework:

- cadastre o processo EDI
- chame por `process_code`
- passe `record` se a origem for interna
- passe `payload` se a origem for externa
- grave a `edi.transaction` no documento de origem quando houver documento do Odoo

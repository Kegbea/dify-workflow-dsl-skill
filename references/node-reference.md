# Node authoring reference

The snippets show the node `data` payload only. Wrap each payload using the common node wrapper and copy version-sensitive fields from a matching Dify export.

## Start

Workflow Start declares external inputs:

```yaml
title: Start
type: start
variables:
  - label: Input
    variable: input_text
    type: paragraph
    required: true
    max_length: 50000
```

Pure Chatflow Start normally uses `variables: []` and reads chat system variables downstream.

## End

Use only for `workflow` normal outputs:

```yaml
title: End
type: end
outputs:
  - variable: result
    value_selector: [generate_result, text]
    value_type: string
```

## Answer

Use for `advanced-chat` visible responses:

```yaml
title: Answer
type: answer
answer: "{{#generate_answer.text#}}"
variables: []
```

## LLM

```yaml
title: Generate
type: llm
model:
  provider: PROVIDER_FROM_EXPORT
  name: MODEL_FROM_EXPORT
  mode: chat
  completion_params:
    temperature: 0.2
prompt_template:
  - id: PROMPT_UUID
    role: system
    text: "Follow the required output contract."
  - id: PROMPT_UUID_2
    role: user
    text: "{{#start.input_text#}}"
context:
  enabled: false
  variable_selector: []
memory:
  role_prefix: {assistant: "", user: ""}
  window: {enabled: false, size: 10}
vision:
  enabled: false
  configs:
    variable_selector: []
```

Use `{{#sys.query#}}` in the user prompt only for Chatflow. Preserve exact model provider and dependency fields from a working export.

## Code

```yaml
title: Normalize
type: code
code_language: python3
code: |
  def main(value):
      return {"result": str(value or "").strip()}
variables:
  - variable: value
    value_selector: [start, input_text]
outputs:
  result:
    type: string
    children: null
```

Compile the code. Ensure each function input has a variable binding and every return key is declared.

## IF/ELSE

```yaml
title: Route
type: if-else
cases:
  - id: "true"
    case_id: "true"
    logical_operator: and
    conditions:
      - id: CONDITION_UUID
        variable_selector: [normalize, result]
        comparison_operator: not empty
        value: ""
        varType: string
```

Each case edge uses its `case_id` as `sourceHandle`. The default edge uses `false`. Every case ID and condition ID must be stable and unique.

## Question Classifier

```yaml
title: Classify intent
type: question-classifier
query_variable_selector: [sys, query]
classes:
  - id: order
    name: Order query
  - id: other
    name: Other
instruction: "Choose exactly one class."
model:
  provider: PROVIDER_FROM_EXPORT
  name: MODEL_FROM_EXPORT
  mode: chat
  completion_params: {temperature: 0}
vision: {enabled: false}
```

Outgoing edge handles are class IDs.

## Parameter Extractor

```yaml
title: Extract fields
type: parameter-extractor
query: [source_node, text]
instruction: "Extract only fields supported by the input."
parameters:
  - name: order_id
    description: Order identifier
    required: false
    type: string
model:
  provider: PROVIDER_FROM_EXPORT
  name: MODEL_FROM_EXPORT
  mode: chat
  completion_params: {temperature: 0}
reasoning_mode: prompt
vision: {enabled: false}
```

## Variable Aggregator

```yaml
title: Merge branches
type: variable-aggregator
output_type: string
variables:
  - [branch_a, result]
  - [branch_b, result]
```

Use only for mutually exclusive branches or version-supported aggregation semantics. Do not mistake aggregation for arbitrary parallel synchronization.

## HTTP Request

```yaml
title: Fetch data
type: http-request
method: get
url: "{{#env.API_BASE_URL#}}/items/{{#start.item_id#}}"
headers: "Accept: application/json"
params: ""
body: {type: none, data: []}
authorization: {type: no-auth}
timeout: {connect: 10, read: 60, write: 10}
retry_config: {retry_enabled: false}
```

Known outputs commonly include `body`, `status_code`, `headers`, and `files`; confirm against the target version. Put credentials in Dify authorization or Secret environment variables.

## Knowledge Retrieval

Knowledge, embedding, and reranking configuration is workspace-bound. Copy the complete node data from a target export, replace only the intended query selector and user-approved dataset bindings, and preserve its dependencies. Do not publish private dataset IDs.

## Tool

Tool fields and outputs are plugin-defined. Copy `provider_id`, `provider_name`, `provider_type`, `tool_name`, `tool_label`, parameter schemas, configurations, and dependency identity from a matching export or plugin package. If unavailable, produce a clearly marked draft placeholder rather than a fabricated import-ready claim.

## Document Extractor and List Operator

Use the exported `variable_selector`/`variable` representation for the target version. Check file cardinality: a node expecting one file must not receive a list without selection or iteration.

## Assigner

Use only in Chatflow unless a target version explicitly supports another workflow-variable pattern. Assigner schemas have changed across Dify versions; copy the current export shape, especially whether source values live in `items[].value` or another selector field.

## Iteration, Loop, Human Input, triggers, and Agent

These have container, branch, package, or version-specific schemas. Read `containers.md` and require a matching official source model or target export before claiming import compatibility.


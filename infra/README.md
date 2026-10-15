# infra/

Plantilla CloudFormation del MVP de Kimün (`plantilla.yaml`), stack `kimun-mvp` en us-east-1.

## Validar

cfn-lint está instalado fuera del repo, en un venv propio (no va en `requirements.txt`):

```fish
~/.local/share/kimun-tools/cfn-lint-venv/bin/cfn-lint infra/plantilla.yaml
aws cloudformation validate-template --template-body file://infra/plantilla.yaml --region us-east-1
```

Para reinstalarlo: `python3 -m venv ~/.local/share/kimun-tools/cfn-lint-venv` y `~/.local/share/kimun-tools/cfn-lint-venv/bin/pip install cfn-lint==1.57.2`.

## Crear el stack

Requiere `CAPABILITY_NAMED_IAM` porque el rol y el instance profile tienen nombre fijo.

```fish
aws cloudformation create-stack --stack-name kimun-mvp --template-body file://infra/plantilla.yaml --capabilities CAPABILITY_NAMED_IAM --region us-east-1
aws cloudformation wait stack-create-complete --stack-name kimun-mvp --region us-east-1
aws cloudformation describe-stacks --stack-name kimun-mvp --region us-east-1 --query 'Stacks[0].Outputs'
```

## Pendiente fuera de la plantilla

- El parámetro SecureString `/kimun/django-secret-key` no lo crea CloudFormation (`AWS::SSM::Parameter` no admite SecureString). La instancia solo puede leerlo.
- Para borrar el stack, primero hay que vaciar el bucket (`aws s3 rm s3://kimun-mvp-<cuenta> --recursive`). Si no, el borrado queda en `DELETE_FAILED`.
- Los trabajos de Transcribe y los vocabularios deben llamarse `kimun-*`, y la salida de Transcribe debe ir a `transcripciones/` del bucket. Así lo exigen los permisos del rol.

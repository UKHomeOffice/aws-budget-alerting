.PHONY: build check-env clean delete-stack package rebuild python-test node-test python-lint \
node-lint node-lint-fix venv lint

all: package

rebuild: clean all

clean:
	rm -r .aws-sam || true
	rm -r lambda-src/.aws-sam || true
	rm packaged.yaml || true
	rm template.yaml || true
	rm -r .pytest-cache || true
	rm -r src/__pycache__ || true
	rm -r tests/__pycache__ || true
	rm -r lambda-src/node_modules || true
	rm -r venv || true

build: ./aws-sam/ ./template.yaml

package: ./packaged.yaml
	@ echo Use deploy.sh to deploy the resources

python-test:
	PYTHONPATH=src python -m pytest --rootdir=tests

./lambda-src/node_modules/:
	cd lambda-src && npm install
	cd lambda-src && npm install --only=dev

python-lint:
	find src tests -iname "*.py" | xargs pylint

node-test: ./lambda-src/node_modules/
	cd lambda-src && npm test

node-lint: ./lambda-src/node_modules/
	cd lambda-src && npm run lint

node-lint-fix: ./lambda-src/node_modules/
	cd lambda-src && npm run lint-fix

lint: node-lint python-lint

delete-stack:
	aws cloudformation delete-stack --stack-name budget-alerts
	aws cloudformation wait stack-delete-complete --stack-name budget-alerts

check-env:
	@ if test "$(LAMBDA_PACKAGE_BUCKET)" = "" ; then \
		echo "LAMBDA_PACKAGE_BUCKET not set"; \
		exit 3; \
	fi

./template.yaml: src/aws_budget_alerting.py
	python '$<' > '$@'

./packaged.yaml: check-env ./aws-sam/ ./template.yaml
	# sam package looks for a cloudformation template file called template.yaml in the current folder
	sam package \
	  --output-template-file '$@' \
	  --s3-bucket $(LAMBDA_PACKAGE_BUCKET)

./aws-sam/: ./template.yaml
	sam build

./venv/:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

venv: ./venv/

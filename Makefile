.PHONY: build check-env clean delete-stack package rebuild test

all: package

rebuild: clean all

clean:
	rm -r .aws-sam || true
	rm -r lambda-src/.aws-sam || true
	rm packaged.yaml || true
	rm template.yaml || true
	rm -r .pytest-cache || true

build: ./aws-sam/

package: ./packaged.yaml
	@ echo Use deploy.sh to deploy the resources

test:
	PYTHONPATH=src python -m pytest --rootdir=test

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
	sam build --use-container

COMP=/home/sjoerd/Tic/compiler/ticcomp
SCRIPT=main.tic
OUTPUT=./bin/execme

default:
	@mkdir -p $(dir $(OUTPUT))
	@$(COMP) $(SCRIPT) -o $(OUTPUT)

run: default
	@$(OUTPUT)

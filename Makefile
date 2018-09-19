mac:
	mkdir -p ./tools
	curl -o tools/kubectl_mac https://storage.googleapis.com/kubernetes-release/release/v1.8.6/bin/darwin/amd64/kubectl

linux:
	mkdir -p ./tools
	curl -o tools/kubectl_linux https://storage.googleapis.com/kubernetes-release/release/v1.8.6/bin/linux/amd64/kubectl

build:
	docker build -t kuryr-tester .

run:
	-docker rm -f kuryr-tester
	docker run -d --add-host kubernetes:118.31.50.72  --name kuryr-tester kuryr-tester:latest
	docker logs -f kuryr-tester

test:
	-docker rm -f kuryr-tester-killme
	docker run -it --add-host kubernetes:118.31.50.72 --name kuryr-tester-killme kuryr-tester:latest sh


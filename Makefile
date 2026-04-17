build:
	kubectl create secret generic mongo-secret --from-env-file=.env --namespace feathr --dry-run=client -o yaml > ./k8s/secrets/mongo-secret.yaml
	kubectl apply -f ./k8s/namespace.yaml
	kubectl apply -f ./k8s/secrets/ -R
	kubectl apply -f ./k8s/mongo/ -R
	kubectl apply -f ./k8s/elastic/ -R
	kubectl apply -f ./k8s/api/ -R
	kubectl apply -f ./k8s/networkpolicies/ -R

delete:
	kubectl delete -f ./k8s -R

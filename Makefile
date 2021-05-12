#TAG    			:= $$(git describe --tags)
TAG 			:= latest	
#REGISTRY		:= registry-1.docker.io
USER 			:= aasgreen
PROJECT			:= dash_labelmaker
#REGISTRY_NAME	:= ${REGISTRY}/${PROJECT}/${IMG}

IMG_WEB_SVC    		:= ${USER}/${PROJECT}:${TAG}
IMG_WEB_SVC_JYP    		:= ${USER}/${PROJECT_JYP}:${TAG}

ID_USER					:= ${shell id -u}
ID_GROUP					:= ${shell id -g}
#REGISTRY_WEB_SVC	:= ${REGISTRY}/${PROJECT}/${NAME_WEB_SVC}:${TAG}
.PHONY:

test:
	echo ${IMG_WEB_SVC}
	echo ${TAG}
	echo ${PROJECT}
	echo ${PROJECT}:${TAG}
	echo ${ID_USER}

build_docker: 
	docker build -t ${IMG_WEB_SVC} ./docker

run_docker:
	docker run --shm-size=1g --user="${ID_USER}:${ID_GROUP}" --ulimit memlock=-1 --ulimit stack=67108864 --memory-swap -1 -it -v ${PWD}:/work/ -p 8051:8050 ${IMG_WEB_SVC}

clean: 
	find -name "*~" -delete
	-rm .python_history
	-rm -rf .config
	-rm -rf .cache

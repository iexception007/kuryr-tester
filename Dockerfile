FROM python:2.7

RUN mkdir -p /app/ \
 && mkdir -p /root/.pip/
ADD source/pip.conf   /root/.pip/
RUN pip install kubernetes
RUN pip install python-neutronclient
RUN pip install python-novaclient

ADD ./conf/.kube/config    /root/.kube/
ADD ./kuryr-tester.py      /app/
ADD ./tools/kubectl_linux  /app/
WORKDIR /app/

CMD ["python", "kuryr-tester.py"]
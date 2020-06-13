FROM quay.io/keycloak/keycloak:10.0.1

COPY realm-export.json /tmp/realm-export.json

ENV KEYCLOAK_IMPORT /tmp/realm-export.json

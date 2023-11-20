test failed login

```
curl --location 'http://localhost:8520/token' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--data '{
  "username": "{{username}}",
  "password": "{{password}}"
}'
```

test ok login

```
curl --location 'http://localhost:8520/token' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--data '{
  "username": "{{username}}",
  "password": "{{password}}"
}'
```



test get client

```
curl --location 'http://localhost:8520/clientes' \
--header 'Authorization: Bearer e618f6127da5d4495b8ecd688ba39282' \
--data ''
```

test_max_failed_attempts

```
test login 4 veces
```


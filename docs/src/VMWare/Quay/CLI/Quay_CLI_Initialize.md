To create the initial Quay user using the `FEATURE_USER_INITIALIZE` option, the API must be used. In order to do this, create a JSON file with a description of the user similar to the following:

```
{
    "username": "quayadmin",
    "password":"password123",
    "email": "quayadmin@example.com",
    "access_token": true
}
```

The `access_token` is optional, but could be useful for login later down the line. With the JSON file created, a POST to the API needs to be completed to create the user:

```
 curl -X POST -k \
  https://central-quay-registry.apps.ocp4.example.com/api/v1/user/initialize \
  --header "Content-Type: application/json" \
  --data @quayadmin-user.json
```

You should receive a response which includes an access token and an encrypted password. You can use this `access_token` to create organizations, repositories, robot users and several other objects in Quay **assuming** the user created is part of the `SUPER_USERS` option in the `init-config-bundle-secret`, otherwise the secret will need to be edited using the `oc` tooling in order to have any administrative access to the Quay registry.
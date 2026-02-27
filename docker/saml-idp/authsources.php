<?php

$config = [

    // This is the authentication source which handles admin authentication.
    'admin' => [
        'core:AdminPassword',
    ],

    // Test users for development
    'example-userpass' => [
        'exampleauth:UserPass',

        // Test users with different roles
        'admin:admin' => [
            'uid' => ['admin'],
            'eduPersonAffiliation' => ['admin', 'staff'],
            'email' => ['admin@example.com'],
            'displayName' => ['Admin User'],
            'givenName' => ['Admin'],
            'sn' => ['User'],
            'netid' => ['admin'],
        ],
        'user:user' => [
            'uid' => ['user'],
            'eduPersonAffiliation' => ['member', 'staff'],
            'email' => ['user@example.com'],
            'displayName' => ['Regular User'],
            'givenName' => ['Regular'],
            'sn' => ['User'],
            'netid' => ['user'],
        ],
        'testuser:testuser' => [
            'uid' => ['testuser'],
            'eduPersonAffiliation' => ['member', 'student'],
            'email' => ['testuser@example.com'],
            'displayName' => ['Test User'],
            'givenName' => ['Test'],
            'sn' => ['User'],
            'netid' => ['testuser'],
        ],
        'test:test' => [
            'uid' => ['test'],
            'eduPersonAffiliation' => ['member', 'staff'],
            'email' => ['test@example.com'],
            'displayName' => ['Test Account'],
            'givenName' => ['Test'],
            'sn' => ['Account'],
            'netid' => ['test'],
        ],
    ],

];

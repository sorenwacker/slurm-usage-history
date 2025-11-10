<?php

/**
 * SAML 2.0 remote SP metadata for SimpleSAMLphp.
 * This registers our SLURM Dashboard as a Service Provider
 */

$metadata['http://localhost:8100/saml/metadata'] = [
    'AssertionConsumerService' => 'http://localhost:8100/saml/acs',
    'SingleLogoutService' => 'http://localhost:8100/saml/sls',
    'NameIDFormat' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',

    // Attributes to release to the SP
    'attributes' => [
        'uid',
        'email',
        'displayName',
        'givenName',
        'sn',
        'eduPersonAffiliation',
        'netid',
    ],

    // Optional: Attribute mappings
    'attributes.NameFormat' => 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic',

    // Sign assertions
    'assertion.encryption' => false,
    'nameid.encryption' => false,
];

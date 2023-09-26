<?php
/*
 This is used for local development only.
*/
$config = array(

    'admin' => array(
        'core:AdminPassword',
    ),

    'example-userpass' => array(
        'exampleauth:UserPass',
        'jkh@magenta43dk.onmicrosoft.com:admin' => array(
            'email' => 'jkh@magenta43dk.onmicrosoft.com',
            'username' => 'jkh@magenta43dk.onmicrosoft.com',
            'first_name' => 'Jonas Kofoed',
            'last_name' => 'Hansen',
            'sid' => 'S-DIG',
        ),
        'af@magenta43dk.onmicrosoft.com:admin' => array(
            'email' => 'af@magenta43dk.onmicrosoft.com',
            'username' => 'af@magenta43dk.onmicrosoft.com',
            'first_name' => 'Alexander "El Jefe"',
            'last_name' => 'Faithfull',
            'sid' => 'Familierådgivning',
        ),
        'jdk@magenta43dk.onmicrosoft.com:admin' => array(
            'email' => 'jdk@magenta43dk.onmicrosoft.com',
            'username' => 'jdk@magenta43dk.onmicrosoft.com',
            'first_name' => 'Jesper Dam',
            'last_name' => 'Knudgaard',
            'sid' => 'Familierådgivning',
        ),
        'datascanner-admin@magenta43dk.onmicrosoft.com:admin' => array(
            'email' => 'datascanner-admin@magenta43dk.onmicrosoft.com',
            'username' => 'datascanner-admin@magenta43dk.onmicrosoft.com',
            'first_name' => 'admin',
            'last_name' => 'datascanner',
            'sid' => 'Ungerådgivning',
        ),
        'ungeraadgiver:sagsbehandler' => array(
            'email' => 'user6@example.com',
            'username' => 'ungeraadgiver',
            'first_name' => 'Unge',
            'last_name' => 'Raadgiver',
            'sid' => 'Ungerådgivning',
        ),
        'heidi:heidi' => array(
            'email' => 'hbb@example.dk',
            'username' => 'heidi',
            'first_name' => 'Heidi',
            'last_name' => 'Engelhardt Bebe',
            'sid' => 'S-DIG',
        ),
        'regelmotor:regelmotor' => array(
            'email' => 'user7@example.com',
            'username' => 'regelmotor',
            'first_name' => 'regelmotor',
            'last_name' => 'regelmotor',
            'sid' => 'S-DIG',
        ),
    ),

);

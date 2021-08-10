# Creating Django superusers

The Django apps use Django's normal access control mechanisms. To create a
user with full privileges, use the `createsuperuser` command for each app:

- For the ["raw" install](installation.md):
     - `bin/manage-admin createsuperuser`
     - `bin/manage-report createsuperuser`
- For the [docker-based install](installation.md) (using `docker-compose`):
     - `<docker-compose exec admin> python manage.py createsuperuser`
     - `<docker-compose exec report> python manage.py createsuperuser`

The `createsuperuser` command will prompt for a username, an email
address, and a password for the new accounts.

(Once a superuser account has been created, it can be used in the Django
administration interface to create accounts with more granular permissions.)


# Using the administration interface


## Logging in to the administration interface

The administration interface can be found at `http://<your admin domain>:8020`.


## Creating an organisation

This interface has been designed to support several customers at once, so many
types of object must have an *organisation* associated with them. There is no
default organisation, so create one by logging in to the Django administration
site at `http://<your admin domain>:8020/admin/` with the new superuser account
and then selecting the *Add* option under *OS2Datascanner → Organizations*.


# Using the report interface


## Logging in to the report interface

The report interface can be found at `http://<your admin domain>:8040`.


# Rules

Matches are found from rules.


## CPR

OS2Datascanner comes with a predefined `CPR` rule. This rule will match a
10-digit number, validate that the first six digit is a valid birth date,
perform [modulus 11 check
https://cpr.dk/cpr-systemet/opbygning-af-cpr-nummeret]{.title-ref} respecting
exceptions to this check.

Further checks are enabled by default, giving the match a probability score.


### Context

If the CPR rule finds a number that looks like a CPR, the context around the
number can be further examined to give a probability score.

The context checker is based on simple heuristics rules, estimating a
probability that the number is a CPR based on the words before and after.

`pre` refers to approximately two words before-, and `post` two words after the
CPR

-   Does `pre` contains `p-nr:` or variants; example `p-nummer 111111-1118`
-   Are there unbalanced delimiters `(,{,[,<` around; example `{111111-1118`
    whereas `{111111-1118}` does not change the probability. Note that
    `{111111-1118 Anders}` is considered unbalanced. Whitespace is ignored.
-   Is there a number before or after that does not resemble another CPR;
    example `220 111111-1118`
-   Is there a unitary operator `-,+` or symbol `!,#` around; example
    `+111111-1118`
-   Are sourrounding words written with a mixing of cases; example `mAgenTa
    111111-1118`, whereas `Magenta`, `magenta` or `MAGENTA` does not change the
    probability.

results in `probability=0`.

If `pre` or `post` contains `CPR` (case insensitive) results in `probability=1`

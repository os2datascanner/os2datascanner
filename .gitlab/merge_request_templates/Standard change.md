## What does this MR do?
<!--
Describe what this MR is about AND how to test it.
Include any points that reviewers should pay special attention to.

If any UI changes have been made, please include screenshots.
-->

<!-- sets current user as assignee -->
/assign me
/milestone %"Next Release"
<!-- Other recommended quick actions (remove # to apply):
#/request_review @af @jkh @tha @jdk @rkk @nsn @sos
#/label ~bug
#/label ~feature

-->

## Author's checklist
<!--
MRs must be marked as WIP until all checkboxes have been filled.
Checkboxes can be pre-filled before submitting the MR by replacing
[ ] with [x],
-->
- [ ] Workflow:
    - [ ] The title of this MR contains the relevant ticket no., formatted like `[#12345]`
    - [ ] The corresponding Redmine ticket has been set to `Needs review`, assigned to the principal reviewer and contains a link to MR
    - [ ] The MR has been labelled with either ~bug (if it is a bugfix) or ~enhancement (if it is a feature)
- [ ] Maintainability:
    - [ ] I have rebased/squashed the code into a minimal amount of atomic commits that reference the ticket ID (eg. `[#12345] Implement featureX in Y`)
    - [ ] I have ensured the MR does not introduce indentation or charset issues
    - [ ] I have added or updated documentation where relevant
    - [ ] I have added unit tests or made a conscious decision not to
- [ ] UI (if relevant):
    - [ ] I have added screenshots of the most significant UI changes to the MR description
    - [ ] I have tested all UI changes in:
        - [ ] Firefox
        - [ ] Chrome
        - [ ] Safari
- [ ] QA:
    - [ ] I have tested the feature/bugfix manually
    - [ ] I have added/updated and verified translations where relevant
    - [ ] I have run any new migrations on a non-empty database
    - [ ] I have updated the CHANGELOG.md file to reflect the changes made

## Review checklist

- [ ] The code is understandable, well-structured and sufficiently documented
- [ ] I would be able to test this feature and verify that it's working without further input from the author
- [ ] I have either checked out the code and tested it locally or thoroughly vetted it

## On Merge
- [ ] Update redmine:
    - [ ] Status (to `Done`)
    - [ ] Version (upcoming release)
    - [ ] Assignee (if relevant)

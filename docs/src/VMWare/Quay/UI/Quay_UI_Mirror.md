Enabling Mirroring in Quay is still a manual process. Because Quay on OpenShift relies heavily on its Postgres database for state syncing and its ability to scale (not to mention Geo Replications), it is currently not possible to do a bulk import of mirror definitions.

## Mirror Prerequisite

Only repositories in an organization can be mirrored. In order to create an organization, login to Quay as a `superuser`. On the main page there is a `+` sign on the far right hand panel which says `Create New Organization`.

![quay_mirror_create_org.png](../../images/quay_mirror_create_org.png)

Simply choose the name for the organization and click `Create Organization`.

![quay_mirror_create_org2.png](../../images/quay_mirror_create_org2.png)

> [!NOTE] 
> Organizations rely heavily of their use of `teams` and `owners`. An organization is only visible to its' team members of organization owners.

## OpenShift Quay Mirror Config

> [!IMPORTANT]
> Both the ` FEATURE_REPO_MIRROR: true` in the `init-config-bundle-secret` and the `mirror` option to `managed: true` in the `QuayRegistry` object must be set

In order to edit the QuayRegistry object from the UI, click on **Operators --> Installed Operators --> Red Hat Quay --> ⋮ --> Edit QuayRegistry**

![quay_mirror_ocp1.png](../../images/quay_mirror_ocp1.png)

From there, either use the form view or the YAML view to ensure that the `mirror` option is managed by the Quay Operator.

## Quay Test Repo

For this guide, create a test repo inside of the `example-org`. To do so, simply click on the `+ Create New Repository` button.

![quay_mirror_repo.png](../../images/quay_mirror_repo.png)

Choose a name for the repo and decide whether or not it should be public.

> [!NOTE]
> If the feature flag `FEATURE_ANONYMOUS_ACCESS` is set to `false` even public repositories will require authentication to pull images. (If unspecified this defaults to `true`)

![quay_mirror_repo2.png](../../images/quay_mirror_repo2.png)

Once the organization has a repo, click on the circular arrows which indicate mirror configuration. By default newly created repos are not created as a mirror.

> [!WARNING]
> If a repo is set as a mirror, Quay treats it as read only! This means the only user that an write images to the repo is the robot account used to initial the mirror.

![quay_mirror_repo3.png](../../images/quay_mirror_repo3.png)

To set a repo to the `Mirror` state, select the gear icon on the left to edit the settings of a repo. Under `Repository State` change the drop down from `Normal` to `Mirror`.

![quay_mirror_repo4.png](../../images/quay_mirror_repo4.png)

Finally go back to the `Repository Mirror` section (indicated by the circular arrows on the left hand panel) and fill out the information.

> [!NOTE]
> The Robot user is the user Quay will allow to write to the read-only mirror. If one does not exist, the dropdown here will allow you to create one. 

![quay_mirror_repo5.png](../../images/quay_mirror_repo5.png)

Click `Enable Mirror` to complete the configuration of this repository. 
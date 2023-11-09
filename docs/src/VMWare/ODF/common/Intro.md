# Introduction

In order to install and successfully configure Quay as a reliable enterprise registry, a solid storage solution needs to be provided. While it is possible to bring an 3rd party storage provider into the equation. This guide focuses on standing up OpenShift Data Foundation. Both the storage preparation and the installation and configuration can both be done via the commandline `oc` utility as well as through the OpenShift Console.

The commandline is more automatable and focuses on creating the required `yaml` files in order to deploy all of the required components with predefined options selected ahead of time and built into the deployment process.

The UI provides a more approachable way to discover the options which may be available. These options are often exposed in a wizard style format and can help users figure out what configurations are available for a given choice.

This specific guide is focused solely on options relevant to deploy to OpenShift 4.x on top of VMWare. While there is a lot of overlap for other deployment types (AWS, GCP, Azure etc) their specifics might vary wildly and therefore this guide should only be used as a rough approximation of how one might go about configuration Quay with ODF on other providers.
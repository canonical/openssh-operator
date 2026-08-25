Feature: Functional edge tests
  Functional tests for the edge risk level


  @functional @edge
  Scenario: Deploy the OpenSSH charm with a principal charm
    Given I pack an 'openssh' charm
    And I add model 'openssh'
    And I switch to model 'openssh'
    And I deploy 'openssh' from a local charm located at 'openssh.charm'
    And I deploy 'ubuntu' on base 'ubuntu@26.04' from channel 'latest/stable'
    And I integrate 'openssh:juju-info' with 'ubuntu:juju-info'
    Then all agents are 'idle' in model 'openssh'
    And the workload status for app 'openssh' is 'active'
    And the workload status message for app 'openssh' is ''
  Scenario: Change the OpenSSH log level
    Given 'openssh' is deployed
    And I set 'log-level' for app 'openssh' to 'verbose'
    Then all agents are 'idle' in model 'openssh'
    And the workload status for app 'openssh' is 'active'
  Scenario: Change the OpenSSH port number
    Given 'openssh' is deployed
    And I set 'port' for app 'openssh' to '2222'
    Then all agents are 'idle' in model 'openssh'
    And the workload status for app 'openssh' is 'active'
  Scenario: Reset the OpenSSH port to the default
    Given 'port' for app 'openssh' is set to '2222'
    And I set 'port' for app 'openssh' to '22'
    Then all agents are 'idle' in model 'openssh'
    And the workload status for app 'openssh' is 'active'

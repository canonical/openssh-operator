Feature: Solution edge tests
  Solution tests for the edge risk level


  @solution @edge
  Scenario: Integrate OpenSSH with SSSD
    Given I deploy 'sssd' from channel 'latest/edge' on base 'ubuntu@26.04'
    And I integrate 'sssd:juju-info' with 'bare:juju-info'
    And I integrate 'sssd:ssh-config' with 'openssh:ssh-config'
    And the workload status for app 'sssd' is 'waiting'
    And all agents are 'idle' in model 'openssh'
    And I wait for '30' seconds
    When I execute 'cat /etc/ssh/ssh_config.d/99-charmed-openssh-*.conf' on unit 'openssh/0'
    Then the output should contain 'AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys'

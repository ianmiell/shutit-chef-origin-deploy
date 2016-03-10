"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class shutit_chef_origin_deploy(ShutItModule):


	def build(self, shutit):
		# Some useful API calls for reference. See shutit's docs for more info and options:
		#
		# ISSUING BASH COMMANDS
		# shutit.send(send,expect=<default>) - Send a command, wait for expect (string or compiled regexp)
		#                                      to be seen before continuing. By default this is managed
		#                                      by ShutIt with shell prompts.
		# shutit.multisend(send,send_dict)   - Send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.send_and_get_output(send)   - Returns the output of the sent command
		# shutit.send_and_match_output(send, matches) 
		#                                    - Returns True if any lines in output match any of 
		#                                      the regexp strings in the matches list
		# shutit.send_until(send,regexps)    - Send command over and over until one of the regexps seen in the output.
		# shutit.run_script(script)          - Run the passed-in string as a script
		# shutit.install(package)            - Install a package
		# shutit.remove(package)             - Remove a package
		# shutit.login(user='root', command='su -')
		#                                    - Log user in with given command, and set up prompt and expects.
		#                                      Use this if your env (or more specifically, prompt) changes at all,
		#                                      eg reboot, bash, ssh
		# shutit.logout(command='exit')      - Clean up from a login.
		# 
		# COMMAND HELPER FUNCTIONS
		# shutit.add_to_bashrc(line)         - Add a line to bashrc
		# shutit.get_url(fname, locations)   - Get a file via url from locations specified in a list
		# shutit.get_ip_address()            - Returns the ip address of the target
		# shutit.command_available(command)  - Returns true if the command is available to run
		#
		# LOGGING AND DEBUG
		# shutit.log(msg,add_final_message=False) -
		#                                      Send a message to the log. add_final_message adds message to
		#                                      output at end of build
		# shutit.pause_point(msg='')         - Give control of the terminal to the user
		# shutit.step_through(msg='')        - Give control to the user and allow them to step through commands
		#
		# SENDING FILES/TEXT
		# shutit.send_file(path, contents)   - Send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath)
		#                                    - Send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath)
		#                                    - Send directory and contents to path on the target
		# shutit.insert_text(text, fname, pattern)
		#                                    - Insert text into file fname after the first occurrence of 
		#                                      regexp pattern.
		# shutit.delete_text(text, fname, pattern)
		#                                    - Delete text from file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.replace_text(text, fname, pattern)
		#                                    - Replace text from file fname after the first occurrence of
		#                                      regexp pattern.
		# ENVIRONMENT QUERYING
		# shutit.host_file_exists(filename, directory=False)
		#                                    - Returns True if file exists on host
		# shutit.file_exists(filename, directory=False)
		#                                    - Returns True if file exists on target
		# shutit.user_exists(user)           - Returns True if the user exists on the target
		# shutit.package_installed(package)  - Returns True if the package exists on the target
		# shutit.set_password(password, user='')
		#                                    - Set password for a given user on target
		#
		# USER INTERACTION
		# shutit.get_input(msg,default,valid[],boolean?,ispass?)
		#                                    - Get input from user and return output
		# shutit.fail(msg)                   - Fail the program and exit with status 1
		# 
		shutit.send('rm -rf /tmp/shutit_chef_origin_deploy')
		shutit.send('mkdir -p /tmp/shutit_chef_origin_deploy')
		shutit.send('cd /tmp/shutit_chef_origin_deploy')
		shutit.send('vagrant init centos/7')
		shutit.send('vagrant up --provider virtualbox')                                                                                                                       
		shutit.login(command='vagrant ssh')                                                                                                                                   
		shutit.login(command='sudo su -',note='Become root')


		############################################################
		# This installer is suitable for a standalone installation #
		# "All in the box" (Master and Node in a server)           #
		############################################################
		### In vagrant box
		shutit.send('sed -i "/' + shutit.cfg[self.module_id]['server_ip'] + '/d" /etc/hosts')
		shutit.send('echo -e "' + shutit.cfg[self.module_id]['server_ip'] + ' ' + shutit.cfg[self.module_id]['server_fqdn'] + '" >> /etc/hosts')
		shutit.send('yum -y update')
		### Create the chef-local mode infrastructure
		shutit.send('mkdir -p chef-solo-example/{backup,cache}')
		shutit.send('cd chef-solo-example')
		shutit.send('''cat << EOF > Gemfile
source "https://rubygems.org"
gem 'knife-solo'
gem 'librarian-chef'
EOF''')
		### Installing dependencies
		shutit.install('rubygem-bundler kernel-devel ruby-devel gcc make git')
		### Installing gems 
		shutit.send('''if [ ! -f ~/.gemrc ]
then 
  echo "gem: --no-document" > ~/.gemrc
fi''')
		shutit.send('bundle')
		### Create a kitchen by knife
		shutit.send('knife solo init .')
		shutit.send('''if [ ! -f Cheffile ]
then
  librarian-chef init
fi''')
		shutit.send('''sed -i '/cookbook-openshift3/d' Cheffile''')
		### Modify the librarian Cheffile for manage the cookbooks
		shutit.insert_text("cookbook 'cookbook-openshift3', :git => 'https://github.com/IshentRas/cookbook-openshift3.git'",'Cheffile')
		shutit.send('librarian-chef install')
		### Create the dedicated environment for Origin deployment
		shutit.send('''cat << EOF > environments/origin.json
{
  "name": "origin",
  "description": "",
  "cookbook_versions": {

  },
  "json_class": "Chef::Environment",
  "chef_type": "environment",
  "default_attributes": {

  },
  "override_attributes": {
    "cookbook-openshift3": {
      "openshift_deployment_type": "origin",
      "master_servers": [
        {
          "fqdn": "''' + shutit.cfg[self.module_id]['server_fqdn'] + '''",
          "ipaddress": "''' + shutit.cfg[self.module_id]['server_ip'] + '''"
        }
      ],
      "node_servers": [
        {
          "fqdn": "''' + shutit.cfg[self.module_id]['server_fqdn'] + '''",
          "ipaddress": "''' + shutit.cfg[self.module_id]['server_ip'] + '''"
        }
      ]
    }
  }
}
EOF''')
		### Create the dedicated role for the Chef run_list
		shutit.send('''cat << EOF > roles/origin.json 
{
  "name": "origin",
  "description": "",
  "default_attributes": {

  },
  "override_attributes": {

  },
  "chef_type": "role",
  "run_list": [
    "recipe[cookbook-openshift3]",
    "recipe[cookbook-openshift3::common]",
    "recipe[cookbook-openshift3::master]",
    "recipe[cookbook-openshift3::node]",
    "recipe[cookbook-openshift3::node_config_post]"
  ],
  "env_run_lists": {

  }
}
EOF''')
		### Specify the configuration details for chef-solo
		shutit.send('''cat << EOF > solo.rb
cookbook_path [
               '/root/chef-solo-example/cookbooks',
               '/root/chef-solo-example/site-cookbooks'
              ]
environment_path '/root/chef-solo-example/environments'
file_backup_path '/root/chef-solo-example/backup'
file_cache_path '/root/chef-solo-example/cache'
log_level :info
log_location STDOUT
solo true
EOF''')
		### Deploy OSE !!!!
		shutit.send('''chef-client -z --environment origin -j roles/origin.json -c ~/chef-solo-example/solo.rb''')
		shutit.send('''if ! $(oc get project test --config=/etc/origin/master/admin.kubeconfig &> /dev/null)
then 
  # Create a demo project
  oadm new-project demo --display-name="Origin Demo Project" --admin=demo
fi''')
		# Reset password for demo user
		shutit.send('htpasswd -b /etc/origin/openshift-passwd demo 1234')
		##### Installation DONE ######
		#####                   ######
		shutit.pause_point('''
Your installation of Origin is completed.

A demo user has been created for you.
Password is : 1234

You can login via : oc login -u demo

Next steps for you (To be performed as system:admin --> oc login -u system:admin):

1) Deploy registry -> oadm registry --service-account=registry --credentials=/etc/origin/master/openshift-registry.kubeconfig --config=/etc/origin/master/admin.kubeconfig
2) Deploy router -> oadm router --service-account=router --credentials=/etc/origin/master/openshift-router.kubeconfig
3) Read the documentation : https://docs.openshift.org/latest/welcome/index.html

You should disconnect and reconnect so as to get the benefit of bash-completion on commands''')
		### Log out of vagrant machine
		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is 
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']
		shutit.get_config(self.module_id,'server_fqdn',default='localhost',hint="Please enter the FQDN of the server, suggestion above: ")
		shutit.get_config(self.module_id,'server_ip',default='127.0.0.1',hint="Please enter the IP of the server")
		return True

	def test(self, shutit):
		# For test cycle part of the ShutIt build.
		return True

	def finalize(self, shutit):
		# Any cleanup required at the end.
		return True
	
	def is_installed(self, shutit):
		return False


def module():
	return shutit_chef_origin_deploy(
		'tk.shutit.shutit_chef_origin_deploy.shutit_chef_origin_deploy', 1845506479.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['tk.shutit.vagrant.vagrant.vagrant']
	)


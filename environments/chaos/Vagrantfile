# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'pp'
require 'set'
require 'fileutils'

# This Vagrant script assumes that you are running on a system with virtualbox
# installed.

########################
# BEGIN HELPER FUNCTIONS
########################

# Get a handle to the filepath of this Vagrantfile. Some file IO will be
# relative to this Vagrantfile's project directory.
filepath = File.expand_path(File.dirname(__FILE__))

# Define the properties filename relative to filepath
properties_filename = File.join("#{filepath}", "config.properties")

# Load the config.properties file
def load_properties(properties_filename)
  properties = {}
  File.open(properties_filename, 'r') do |properties_file|
    properties_file.read.each_line do |line|
      line.strip!
      if (line[0] != ?# and line[0] != ?=)
        i = line.index('=')
        if (i)
          properties[line[0..i - 1].strip] = line[i + 1..-1].strip
        else
          properties[line] = ''
        end
      end
    end      
  end
  properties
end

# Create etc/hosts file
def write_etc_hosts(vagrant_dirname, clientlist, validatorlist)
  dirname = File.join("#{vagrant_dirname}", "etc")
  unless File.directory?(dirname)
    FileUtils.mkdir_p(dirname)
  end
  File.open(File.join("#{dirname}", "hosts"), 'w') do |host_file|
    host_file.write("127.0.0.1       localhost\n")
    host_file.write("127.0.1.1       vagrant\n")
    host_file.write("::1     localhost ip6-localhost ip6-loopback\n")
    host_file.write("ff02::1 ip6-allnodes\n")
    host_file.write("ff02::2 ip6-allrouters\n")
    clientlist.each_with_index do |value, index|
      host_file.write("#{value}    cli#{index + 1}.sovrin.lab cli#{index + 1}\n")
    end
    validatorlist.each_with_index do |value, index|
      host_file.write("#{value}    validator#{index + 1}.sovrin.lab validator#{index + 1} Node#{index + 1}.sovrin.lab Node#{index + 1}\n")
    end
  end
end

# Create pool1 directory and it's contents (less pool_transaction_genesi file)
# The pool_transactions_genesis file will be generated and copied into the
# /home/<user>/pool1 directory during VM provisioning
def create_pool1(vagrant_dirname, clientlist, validatorlist)
  dirname = File.join("#{vagrant_dirname}", "pool1")
  unless File.directory?(dirname)
    FileUtils.mkdir_p(dirname)
  end
  File.open(File.join("#{dirname}", "clients"), 'w') do |clients_file|
    clients_file.write("[")
    clientlist.each_with_index do |value, index|
      if index > 0
        clients_file.write(",")
      end
      clients_file.write("\"cli#{index + 1}\"")
    end
    clients_file.write("]")
  end
  File.open(File.join("#{dirname}", "ssh_config"), 'w') do |ssh_config_file|
    clientlist.each_with_index do |ip, index|
      ssh_config_file.write("Host cli#{index + 1}\n")
      ssh_config_file.write("    User <USERNAME>\n")
      ssh_config_file.write("    Hostname #{ip}\n")
      ssh_config_file.write("    IdentityFile /home/<USERNAME>/.ssh/id_rsa\n")
    end
    validatorlist.each_with_index do |ip, index|
      ssh_config_file.write("Host validator#{index + 1}\n")
      ssh_config_file.write("    User <USERNAME>\n")
      ssh_config_file.write("    Hostname #{ip}\n")
      ssh_config_file.write("    IdentityFile /home/<USERNAME>/.ssh/id_rsa\n")
    end
  end
end

# Get the list of repos from config.properties. Each repo MUST define a 'path'.
# Use the path property to extract the repo name.
def get_repos_from_properties(properties)
  # A set of repos included in properties file
  repos = Set.new []

  # Extract repo names from the 'path' property for each repo
  properties.each do |key, value|
    if key.start_with?("repos.") && key.end_with?(".path")
      # Extract the repo name from the key; replacing dots with dashes.
      repo_property_name = key[6..(key.index('.path')-1)]
      repo_name = repo_property_name.gsub(".", "-")
      repos.add(repo_name)
    end
  end
  #puts "repos"
  #pp repos
  repos
end

########################
# END HELPER FUNCTIONS
########################

# Load the properties hash using config.properties in the root of this Vagrant
# project.
properties = load_properties(properties_filename)
#$stdout.puts "properties=#{properties['client.count']}"

# Client VM config
client_box    = properties['client.box'] || 'bento/ubuntu-16.04'
client_cpus   = properties['client.cpus'] || '1'
client_memory = properties['client.memory'] || '1024'
client_node_count = properties['client.count'] || 1

# Validator VM config
validator_box    = properties['validator.box'] || 'bento/ubuntu-16.04'
validator_cpus   = properties['validator.cpus'] || '1'
validator_memory = properties['client.memory'] || '1024'
validator_node_count = properties['validator.count'] || 4

# Private IP base.
# All client ips will be in the range of 101-156 (56 max)
# All validator ips will be in the range of 201-256 (56 max)
ip_base = '10.20.30'
client_node_base = 100
validator_node_base = 200
# A comma separated list of client ips in the range 10.20.30.101-156
clientiplist = Array.new
# A comma separated list of validator ips in the range 10.20.30.201-256
nodeiplist = Array.new

# TODO: change the 'repo' default back to master
# Cannot use master due to version pinning in master version of sovtoken package
# Both sovtoken and indy-node dep on indy-plenum, libindy, etc. and indy-node
# also pins to a specific version, but a version that only exists in master.
# We can't have two versions of indy-plenum, libindy, etc. Use stable until
# sovtoken changes it's '=' designation to '>='.
#repo = "master"
repo = "stable"

# modify this for your timezone
timezone = '/usr/share/zoneinfo/America/Denver'
sshuser = 'vagrant'

# The user must run the setup.sh script before running 'vagrant up'
# Ensure the ssh directory exists and has expected content
filepath = File.expand_path(File.dirname(__FILE__))
directory = File.join("#{filepath}", "ssh")
if !Dir.exists?(directory)
  $stderr.puts "Please run the setup.sh script to setup the SSH configuration "\
    "for this project."
  $stderr.puts "#{directory} not found."
  exit 1
end

ssh_private_key = File.join("#{directory}", "id_rsa")
ssh_public_key = File.join("#{directory}", "id_rsa.pub")
pemfile = File.join("#{directory}", "chaos.pem")
if !File.exists?("#{ssh_private_key}") ||
   !File.exists?("#{ssh_public_key}") ||
   !File.exists?("#{pemfile}")
  $stderr.puts "The ssh directory in the root of this project does not contain"\
    "all the expected files (id_rsa, id_rsa.pub, and chaos.pem)."
  $stderr.puts "Please run the setup.sh script to setup the SSH configuration "\
    "for this project."
  exit 1
end

# Get a list of development repos
repos = get_repos_from_properties(properties)

Vagrant.configure("2") do |config|
  # Generate clientiplist 
  (1...(client_node_count.chomp.to_i + 1)).step(1) do |n|
    node_num = (client_node_base + n)
    client_ip = "#{ip_base}.#{node_num}"
    #$stdout.puts "client_ip=#{client_ip}"
    clientiplist.push("#{client_ip}")
  end
  # Generate nodeiplist 
  (1...(validator_node_count.chomp.to_i + 1)).step(1) do |n|
    node_num = (validator_node_base + n)
    validator_ip = "#{ip_base}.#{node_num}"
    #$stdout.puts "validator_ip=#{validator_ip}"
    nodeiplist.push("#{validator_ip}")
  end

  #$stdout.puts nodeiplist.join(",")
  write_etc_hosts("#{filepath}", clientiplist, nodeiplist)
  create_pool1("#{filepath}", clientiplist, nodeiplist)
  nodeipcsvstring = nodeiplist.join(",")
  # Converte validator_node_count to to an int
  vnc = validator_node_count.chomp.to_i

  # Instantiate cli1 to up to cli#{n}
  (1...(client_node_count.chomp.to_i + 1)).step(1) do |n|
    clientvmname="cli#{n}"
    node_num = (client_node_base + n)
    clientip = "#{ip_base}.#{node_num}"
    config.vm.define "cli#{n}", autostart: true do |cli|
      cli.vm.box = client_box
      cli.vm.host_name = clientvmname
      cli.vm.network 'private_network', ip: clientip
      cli.ssh.private_key_path = ['ssh/id_rsa', '~/.vagrant.d/insecure_private_key']
      cli.ssh.username = sshuser
      cli.ssh.insert_key = false
      cli.vm.provider "virtualbox" do |vb|
        vb.name   = clientvmname
        vb.gui    = false
        vb.memory = client_memory
        vb.cpus   = client_cpus
        vb.customize ["modifyvm", :id, "--cableconnected1", "on"]
      end
      repos.each do |key|
        property_friendly_key = key.gsub("-", ".")
        path = properties["repos.#{property_friendly_key}.path"]
        path = File.expand_path(path)

        shared_folder_key = "repos.#{property_friendly_key}.sharedfolder.type"
        if properties.key?(shared_folder_key)
          shared_folder_type = properties[shared_folder_key]
          #puts "Shared folder #{path} will be shared as /src/#{key} using #{shared_folder_type}"
          cli.vm.synced_folder "#{path}", "/src/#{key}", type: "#{shared_folder_type}"
        else
          #puts "Shared folder #{path} will be shared as /src/#{key} using default to what Vagrant deems the best synced folder option for your environment."
          cli.vm.synced_folder "#{path}", "/src/#{key}"
        end
      end
      cli.vm.provision "indy", type: "shell", path: "scripts/client.sh", args: [timezone, nodeipcsvstring, vnc, vnc, repo]
    end
  end

  next_port = 9701
  (1...(vnc + 1)).step(1) do |n|
    validatorvmname="validator#{n}"
    node_num = (validator_node_base + n)
    validatorip = "#{ip_base}.#{node_num}"
    nodeport = next_port
    next_port += 1
    clientport = next_port
    next_port += 1
    config.vm.define "validator#{n}", autostart: true do |validator|
      validator.vm.box = validator_box
      validator.vm.host_name = validatorvmname
      validator.vm.network 'private_network', ip: validatorip
      validator.ssh.private_key_path = ['ssh/id_rsa', '~/.vagrant.d/insecure_private_key']
      validator.ssh.username = sshuser
      validator.ssh.insert_key = false
      validator.vm.provider "virtualbox" do |vb|
        vb.name   = validatorvmname
        vb.gui    = false
        vb.memory = validator_memory
        vb.cpus   = validator_cpus
        vb.customize ["modifyvm", :id, "--cableconnected1", "on"]
      end
      repos.each do |key|
        property_friendly_key = key.gsub("-", ".")
        path = properties["repos.#{property_friendly_key}.path"]
        path = File.expand_path(path)

        shared_folder_key = "repos.#{property_friendly_key}.sharedfolder.type"
        if properties.key?(shared_folder_key)
          shared_folder_type = properties[shared_folder_key]
          #puts "Shared folder #{path} will be shared as /src/#{key} using #{shared_folder_type}"
          validator.vm.synced_folder "#{path}", "/src/#{key}", type: "#{shared_folder_type}"
        else
          #puts "Shared folder #{path} will be shared as /src/#{key} using default to what Vagrant deems the best synced folder option for your environment."
          validator.vm.synced_folder "#{path}", "/src/#{key}"
        end
      end
      validator.vm.provision "indy", type: "shell", path: "scripts/validator.sh", args: ["Node#{n}", validatorip, nodeport, validatorip, clientport, timezone, nodeipcsvstring, vnc, vnc, repo]
    end
  end
end

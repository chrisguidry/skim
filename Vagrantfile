Vagrant.configure(2) do |config|
    config.vm.box = "ubuntu/trusty64"
    config.vm.box_check_update = false  # only using this temporarily while on the train

    config.vm.network "private_network", ip: "10.0.4.2"
    config.vm.provider "virtualbox" do |vb|
        vb.memory = "1024"
    end

    #config.vm.synced_folder "../data", "/vagrant_data"

    config.vm.provision "chef_solo" do |chef|
        chef.add_recipe "apt"
        chef.add_recipe "java"
        chef.add_recipe "elasticsearch"
        chef.add_recipe "elasticsearch::plugins"
        chef.add_recipe "simple-kibana"
        chef.json = {
            "java" => {
                "install_flavor" => "openjdk",
                "jdk_version" => 7
            },
            "elasticsearch" => {
                "version" => "1.4.4",
                "cluster" => {
                    "name" => "skim_dev"
                },
                "network" => {
                    "host" => "10.0.4.2"
                },
                "custom_config" => {
                    "script.disable_dynamic" => false
                },
                "plugins" => {
                    "mobz/elasticsearch-head" => {}
                }
            },
            "kibana" => {
                "config" => {
                    "elasticsearch_url" => "http://10.0.4.2:9200"
                }
            }
        }
    end
end

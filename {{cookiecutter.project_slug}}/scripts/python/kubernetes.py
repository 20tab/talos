"""Define kubernetes cluster class."""

from digitalocean.baseapi import BaseAPI


class Cluster(BaseAPI):
    """Cluster management.

    Attributes accepted at creation time:
    Args:
        name (str): A human-readable name for a Kubernetes cluster.
        region (str): The slug identifier for the region where the Kubernetes cluster
        will be created.
        version (str): The slug identifier for the version of Kubernetes used for the
        cluster. See the /v2/kubernetes/options endpoint for available versions.
        auto_upgrade (bool): A boolean value indicating whether the cluster will be
        automatically upgraded to new patch releases during its maintenance window.
        tags (list): A flat array of tag names as strings to be applied to the
        Kubernetes cluster. All clusters will be automatically tagged "k8s" and
        "k8s:$K8S_CLUSTER_ID" in addition to any tags provided by the user.
        maintenance_policy (object): An object specifying the maintenance window policy
        for the Kubernetes cluster (see table below).
        node_pools (list): An object specifying the details of the worker nodes
        available to the Kubernetes cluster (see table below).

    Attributes returned by API:
        id (str): A unique ID that can be used to identify and reference a Kubernetes
        cluster.
        name (str): A human-readable name for a Kubernetes cluster.
        endpoint (str): The base URL of the API server on the Kubernetes master node.
        region (str): The slug identifier for the region where the Kubernetes cluster
        is located.
        version (str): The slug identifier for the version of Kubernetes used for the
        cluster. If set to a minor version (e.g. "1.14"), the latest version within it
        will be used (e.g. "1.14.6-do.1"); if set to "latest", the latest published
        version will be used.
        auto_upgrade (bool): A boolean value indicating whether the cluster will be
        automatically upgraded to new patch releases during its maintenance window.
        ipv4 (str): The public IPv4 address of the Kubernetes master node.
        cluster_subnet (str): The range of IP addresses in the overlay network of the
        Kubernetes cluster in CIDR notation.
        service_subnet (str): The range of assignable IP addresses for services running
        in the Kubernetes cluster in CIDR notation.
        tags (list):s An array of tags applied to the Kubernetes cluster. All clusters
        are automatically tagged "k8s" and "k8s:$K8S_CLUSTER_ID."
        maintenance_policy (object): An object specifying the maintenance window policy
        for the Kubernetes cluster (see table below).
        node_pools (list): An object specifying the details of the worker nodes
        available to the Kubernetes cluster (see table below).
        created_at (str): A time value given in ISO8601 combined date and time format
        that represents when the Kubernetes cluster was created.
        updated_at (str): A time value given in ISO8601 combined date and time format
        that represents when the Kubernetes cluster was last updated.
        status (object): An object containing a "state" attribute whose value is set to
        a string indicating the current status of the node. Potential values include
        running, provisioning, and errored.

    """

    def __init__(self, *args, **kwargs):
        """Define default values."""
        self.id = None
        self.name = None
        self.endpoint = None
        self.region = None
        self.version = None
        self.auto_upgrade = None
        self.ipv4 = None
        self.cluster_subnet = None
        self.service_subnet = None
        self.tags = []
        self.maintenance_policy = None
        self.node_pools = []
        self.created_at = None
        self.updated_at = None
        self.status = None

        # This will load also the values passed
        super(Cluster, self).__init__(*args, **kwargs)

    @classmethod
    def get_object(cls, api_token, cluster_id):
        """Class method that will return a Cluster object by ID.

        Args:
            api_token (str): token
            cluster_id (int): cluster id
        """
        cluster = cls(token=api_token, id=cluster_id)
        cluster.load()
        return cluster

    def load(self):
        """Load cluster information by id."""
        data = self.get_data("kubernetes/clusters/%s" % self.id)
        cluster_dict = data["kubernetes_cluster"]

        # Setting the attribute values
        for attr in cluster_dict.keys():
            setattr(self, attr, cluster_dict[attr])

        return self

    def load_by_name(self, name):
        """Load cluster information by name."""
        data = self.get_data("kubernetes/clusters")
        for cluster in data["kubernetes_clusters"]:
            if cluster["name"] == name:
                self.id = cluster["id"]
                return self.load()
        return None

    def load_credentials(self):
        """Load cluster credentials."""
        data = self.get_data("kubernetes/clusters/%s/credentials" % self.id)
        return data

    def __str__(self):
        """Return cluster string representation."""
        return "<Cluster: %s %s>" % (self.id, self.name)

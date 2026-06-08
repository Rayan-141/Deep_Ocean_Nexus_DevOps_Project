provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "deepocean" {
  metadata {
    name = "deepocean"
  }
}

"""
Clustering algorithms for hierarchical community detection

This module implements GMM (Gaussian Mixture Model) with BIC optimization
for automatic cluster number selection.

Key features:
- Automatic optimal cluster number detection using BIC
- UMAP dimensionality reduction for better clustering
- Soft clustering with probability scores
- Support for hierarchical iterative clustering
"""

import numpy as np
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

try:
    import umap
    from sklearn.mixture import GaussianMixture
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False
    logger.warning("UMAP or sklearn not installed. Hierarchical clustering disabled.")


def get_optimal_clusters(
    embeddings: np.ndarray,
    max_clusters: int = 50,
    min_clusters: int = 2,
    random_state: int = 42
) -> int:
    """
    Find optimal number of clusters using BIC (Bayesian Information Criterion)
    
    The BIC balances model fit with complexity. Lower BIC is better.
    We test different values of k and select the one with minimum BIC.
    
    Args:
        embeddings: Reduced embeddings (n_samples, n_features)
        max_clusters: Maximum number of clusters to test
        min_clusters: Minimum number of clusters to test
        random_state: Random seed for reproducibility
        
    Returns:
        Optimal number of clusters
        
    Example:
        >>> embeddings = np.random.rand(100, 2)
        >>> k = get_optimal_clusters(embeddings)
        >>> print(f"Optimal clusters: {k}")
        Optimal clusters: 5
    """
    if not CLUSTERING_AVAILABLE:
        raise RuntimeError("UMAP or sklearn not installed")
    
    n_samples = len(embeddings)
    max_clusters = min(n_samples, max_clusters)
    
    if max_clusters < min_clusters:
        logger.warning(f"Not enough samples ({n_samples}) for clustering. Using 1 cluster.")
        return 1
    
    bics = []
    tested_k = []
    
    logger.info(f"Testing k from {min_clusters} to {max_clusters}...")
    
    for k in range(min_clusters, max_clusters + 1):
        try:
            gm = GaussianMixture(
                n_components=k,
                random_state=random_state,
                covariance_type='full',
                max_iter=100
            )
            gm.fit(embeddings)
            bic = gm.bic(embeddings)
            bics.append(bic)
            tested_k.append(k)
            
            # Early stopping: if BIC improvement < 0.1%
            if len(bics) > 5:
                recent_improvement = (bics[-6] - bics[-1]) / bics[-6]
                if recent_improvement < 0.001:
                    logger.info(f"Early stopping at k={k} (improvement < 0.1%)")
                    break
                    
        except Exception as e:
            logger.warning(f"Failed to fit GMM with k={k}: {e}")
            continue
    
    if not bics:
        logger.warning("No valid BIC scores found. Using 1 cluster.")
        return 1
    
    optimal_idx = np.argmin(bics)
    optimal_k = tested_k[optimal_idx]
    
    logger.info(f"Optimal k={optimal_k} with BIC={bics[optimal_idx]:.2f}")
    
    return optimal_k


def GMM_cluster(
    embeddings: np.ndarray,
    n_clusters: int = None,
    threshold: float = 0.1,
    random_state: int = 42
) -> Tuple[List[List[int]], int, np.ndarray]:
    """
    Perform GMM clustering with soft assignment
    
    Entities can belong to multiple clusters if their probability
    exceeds the threshold.
    
    Args:
        embeddings: Entity embeddings (n_samples, n_features)
        n_clusters: Number of clusters (if None, auto-detect)
        threshold: Probability threshold for cluster assignment
        random_state: Random seed
        
    Returns:
        Tuple of:
        - labels: List of cluster labels per entity (can be multi-label)
        - n_clusters: Number of clusters used
        - probabilities: Probability matrix (n_samples, n_clusters)
        
    Example:
        >>> embeddings = np.random.rand(100, 128)
        >>> labels, k, probs = GMM_cluster(embeddings, threshold=0.3)
        >>> print(f"Entity 0 belongs to clusters: {labels[0]}")
        Entity 0 belongs to clusters: [0, 2]
    """
    if not CLUSTERING_AVAILABLE:
        raise RuntimeError("UMAP or sklearn not installed")
    
    if n_clusters is None:
        n_clusters = get_optimal_clusters(embeddings, random_state=random_state)
    
    logger.info(f"GMM clustering with k={n_clusters}")
    
    # Fit GMM
    gm = GaussianMixture(
        n_components=n_clusters,
        random_state=random_state,
        covariance_type='full',
        max_iter=200
    )
    gm.fit(embeddings)
    
    # Get probabilities
    probs = gm.predict_proba(embeddings)
    
    # Assign clusters based on threshold (soft clustering)
    labels = []
    for prob_vector in probs:
        # Find all clusters where probability > threshold
        assigned_clusters = np.where(prob_vector > threshold)[0].tolist()
        
        # If no cluster meets threshold, assign to highest probability
        if not assigned_clusters:
            assigned_clusters = [np.argmax(prob_vector)]
        
        labels.append(assigned_clusters)
    
    logger.info(f"Clustering complete. Avg clusters per entity: {np.mean([len(l) for l in labels]):.2f}")
    
    return labels, n_clusters, probs


def perform_clustering(
    embeddings: np.ndarray,
    reduction_dimension: int = 2,
    cluster_threshold: float = 0.1,
    max_clusters: int = 50,
    random_state: int = 42
) -> Tuple[List[List[int]], int, np.ndarray, np.ndarray]:
    """
    Complete clustering pipeline: UMAP reduction + GMM clustering
    
    This is the main function to use for hierarchical clustering.
    
    Args:
        embeddings: High-dimensional embeddings (n_samples, embedding_dim)
        reduction_dimension: UMAP target dimensions (default: 2)
        cluster_threshold: GMM probability threshold
        max_clusters: Maximum clusters to test
        random_state: Random seed
        
    Returns:
        Tuple of:
        - labels: Cluster assignments
        - n_clusters: Number of clusters
        - reduced_embeddings: UMAP-reduced embeddings
        - probabilities: GMM probabilities
        
    Example:
        >>> embeddings = np.random.rand(1000, 1536)  # OpenAI embeddings
        >>> labels, k, reduced, probs = perform_clustering(embeddings)
        >>> print(f"Clustered {len(embeddings)} entities into {k} communities")
    """
    if not CLUSTERING_AVAILABLE:
        raise RuntimeError("UMAP or sklearn not installed")
    
    n_samples = len(embeddings)
    
    logger.info(f"Starting clustering pipeline for {n_samples} entities")
    
    # Step 1: UMAP dimensionality reduction
    logger.info(f"UMAP reduction to {reduction_dimension}D...")
    reducer = umap.UMAP(
        n_components=reduction_dimension,
        random_state=random_state,
        n_neighbors=min(15, n_samples - 1),
        min_dist=0.1,
        metric='cosine'
    )
    reduced_embeddings = reducer.fit_transform(embeddings)
    
    logger.info(f"UMAP complete. Shape: {reduced_embeddings.shape}")
    
    # Step 2: GMM clustering with BIC optimization
    labels, n_clusters, probs = GMM_cluster(
        reduced_embeddings,
        n_clusters=None,  # Auto-detect
        threshold=cluster_threshold,
        random_state=random_state
    )
    
    return labels, n_clusters, reduced_embeddings, probs


def calculate_cluster_sparsity(labels: List[List[int]], n_entities: int) -> float:
    """
    Calculate cluster sparsity (stop condition for hierarchical clustering)
    
    Sparsity = 1 - (total_assignments / (n_entities * n_clusters))
    Higher sparsity means fewer entities per cluster.
    
    Args:
        labels: Cluster assignments
        n_entities: Total number of entities
        
    Returns:
        Sparsity score (0-1)
    """
    if not labels or n_entities == 0:
        return 1.0
    
    # Count total assignments (entities can belong to multiple clusters)
    total_assignments = sum(len(l) for l in labels)
    
    # Find number of unique clusters
    unique_clusters = set()
    for label_list in labels:
        unique_clusters.update(label_list)
    n_clusters = len(unique_clusters)
    
    if n_clusters == 0:
        return 1.0
    
    # Calculate sparsity
    max_possible_assignments = n_entities * n_clusters
    sparsity = 1.0 - (total_assignments / max_possible_assignments)
    
    return sparsity


if __name__ == "__main__":
    # Test clustering
    logging.basicConfig(level=logging.INFO)
    
    if CLUSTERING_AVAILABLE:
        # Generate test data
        np.random.seed(42)
        test_embeddings = np.random.rand(100, 128)
        
        print("Testing clustering pipeline...")
        labels, k, reduced, probs = perform_clustering(test_embeddings)
        
        print(f"\nResults:")
        print(f"- Number of clusters: {k}")
        print(f"- Reduced embeddings shape: {reduced.shape}")
        print(f"- Sample entity 0 clusters: {labels[0]}")
        print(f"- Sample entity 0 probabilities: {probs[0][:3]}...")
        
        sparsity = calculate_cluster_sparsity(labels, len(test_embeddings))
        print(f"- Cluster sparsity: {sparsity:.3f}")
    else:
        print("Clustering not available. Install: pip install umap-learn scikit-learn")

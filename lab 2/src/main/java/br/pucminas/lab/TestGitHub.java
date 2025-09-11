package br.pucminas.lab;

import org.kohsuke.github.*;
import java.io.*;
import java.util.*;

public class TestGitHub {
    public static void main(String[] args) {
        try {
            // Carregar token
            Properties config = new Properties();
            config.load(new FileInputStream("config.properties"));
            String githubToken = config.getProperty("github.token");
            
            if (githubToken == null || githubToken.trim().isEmpty()) {
                System.out.println("ERRO: Token do GitHub não configurado!");
                return;
            }
            
            System.out.println("Conectando ao GitHub...");
            GitHub github = new GitHubBuilder().withOAuthToken(githubToken).build();
            
            System.out.println("Buscando repositórios Java...");
            GHRepositorySearchBuilder searchBuilder = github.searchRepositories()
                    .q("language:java")
                    .sort(GHRepositorySearchBuilder.Sort.STARS)
                    .order(GHDirection.DESC);
            
            PagedSearchIterable<GHRepository> repositories = searchBuilder.list();
            
            int count = 0;
            for (GHRepository repo : repositories) {
                System.out.println((count + 1) + ". " + repo.getFullName() + 
                    " - Stars: " + repo.getStargazersCount() + 
                    " - Forks: " + repo.getForksCount());
                
                count++;
                if (count >= 5) {
                    break;
                }
                
                // Aguardar um pouco entre requisições
                Thread.sleep(1000);
            }
            
            System.out.println("Teste concluído com sucesso! Coletados " + count + " repositórios.");
            
        } catch (Exception e) {
            System.out.println("ERRO: " + e.getMessage());
            e.printStackTrace();
        }
    }
}

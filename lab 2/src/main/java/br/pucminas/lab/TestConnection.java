package br.pucminas.lab;

import org.kohsuke.github.*;
import java.io.*;
import java.util.*;

public class TestConnection {
    public static void main(String[] args) {
        try {
            // Carregar token
            Properties config = new Properties();
            config.load(new FileInputStream("config.properties"));
            String githubToken = config.getProperty("github.token");
            
            System.out.println("Token configurado: " + (githubToken != null ? "SIM" : "NÃO"));
            
            if (githubToken == null || githubToken.trim().isEmpty()) {
                System.out.println("ERRO: Token do GitHub não configurado!");
                return;
            }
            
            System.out.println("Conectando ao GitHub...");
            GitHub github = new GitHubBuilder().withOAuthToken(githubToken).build();
            
            System.out.println("Verificando informações do usuário autenticado...");
            GHMyself myself = github.getMyself();
            System.out.println("Usuário: " + myself.getLogin());
            System.out.println("Limite de requisições: " + github.getRateLimit().getCore().getRemaining() + "/" + github.getRateLimit().getCore().getLimit());
            
            System.out.println("Teste de conectividade OK!");
            
        } catch (Exception e) {
            System.out.println("ERRO: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
